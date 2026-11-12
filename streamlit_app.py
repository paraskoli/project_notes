"""
Streamlit Web Application for GATE CSE Screenshot Organizer (GATE-Snap).
Allows GATE CSE aspirants to upload/paste screenshots, automatically run OCR,
classify into official GATE CSE subjects, and manage notes.
"""

import os
import io
import time
from pathlib import Path
from PIL import Image
import streamlit as st

from classifier import GATEClassifier, GATE_SUBJECTS
from storage import GATEStorage, DEFAULT_BASE_DIR

# ---------------------------------------------------------
# Page Configuration & Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="GATE-Snap | CSE Screenshot Organizer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished badge and card styling
st.markdown("""
<style>
    .gate-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
        color: white;
        margin-right: 6px;
    }
    .keyword-pill {
        display: inline-block;
        background-color: rgba(100, 116, 139, 0.15);
        color: inherit;
        border: 1px solid rgba(100, 116, 139, 0.3);
        border-radius: 12px;
        padding: 2px 8px;
        margin: 2px 4px 2px 0;
        font-size: 0.8rem;
    }
    .metric-card {
        padding: 16px;
        border-radius: 8px;
        background-color: rgba(128, 128, 128, 0.05);
        border: 1px solid rgba(128, 128, 128, 0.15);
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# State & Helpers
# ---------------------------------------------------------
@st.cache_resource
def get_classifier():
    return GATEClassifier()

@st.cache_resource
def get_storage():
    return GATEStorage()

classifier = get_classifier()
storage = get_storage()

# Subject options helper
SUBJECT_KEYS = list(GATE_SUBJECTS.keys()) + ["General_Notes"]
SUBJECT_NAMES = {
    k: GATE_SUBJECTS[k]["name"] if k in GATE_SUBJECTS else "General Notes & Tips"
    for k in SUBJECT_KEYS
}
SUBJECT_CODES = {
    k: GATE_SUBJECTS[k]["code"] if k in GATE_SUBJECTS else "GEN"
    for k in SUBJECT_KEYS
}
SUBJECT_COLORS = {
    k: GATE_SUBJECTS[k]["color"] if k in GATE_SUBJECTS else "#64748B"
    for k in SUBJECT_KEYS
}


def safe_rerun():
    """Rerun the app safely across different Streamlit versions."""
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()


def show_image(image, **kwargs):
    """Display image with cross-version compatibility."""
    try:
        st.image(image, use_column_width=True, **kwargs)
    except TypeError:
        st.image(image, **kwargs)


def render_subject_badge(subject_id: str, subtopic: str = ""):
    color = SUBJECT_COLORS.get(subject_id, "#64748B")
    name = SUBJECT_NAMES.get(subject_id, subject_id)
    code = SUBJECT_CODES.get(subject_id, "SUB")
    sub_text = f" • {subtopic}" if subtopic and subtopic != "General" else ""
    return f'<span class="gate-badge" style="background-color: {color};">[{code}] {name}{sub_text}</span>'


# ---------------------------------------------------------
# Main App Structure
# ---------------------------------------------------------
def main():
    # Sidebar
    st.sidebar.title("🎯 GATE-Snap")
    st.sidebar.caption("Intelligent Screenshot Organizer for GATE CSE")

    nav_option = st.sidebar.radio(
        "Navigation",
        ["📥 Upload & Classify", "📚 Notes Library & Search", "📊 Preparation Stats", "⚙️ Settings"],
        index=0
    )

    # Sidebar Quick Stats
    st.sidebar.divider()
    stats = storage.get_subject_statistics()
    total_notes = sum(s["count"] for s in stats)
    st.sidebar.metric("Total Saved Notes", f"{total_notes} screenshots")

    st.sidebar.caption("Folder: `~/gate_cse_notes`")

    # Routing
    if nav_option == "📥 Upload & Classify":
        render_upload_page()
    elif nav_option == "📚 Notes Library & Search":
        render_library_page()
    elif nav_option == "📊 Preparation Stats":
        render_stats_page(stats)
    elif nav_option == "⚙️ Settings":
        render_settings_page()


# ---------------------------------------------------------
# View 1: Upload & Classify Page
# ---------------------------------------------------------
def render_upload_page():
    st.header("📥 Upload & Auto-Classify Screenshot")
    st.markdown(
        "Upload or paste a screenshot from lectures, test series, PYQs, or PDFs. "
        "The built-in GATE CSE engine extracts text using OCR and categorizes it into the exact subject folder."
    )

    uploaded_file = st.file_uploader(
        "Choose screenshot image or paste from clipboard (Ctrl+V)",
        type=["png", "jpg", "jpeg", "webp"],
        help="In most modern desktop browsers, click here and press Ctrl+V to paste your clipboard image directly!"
    )

    use_gemini = st.checkbox(
        "Use Gemini Vision AI (if API key is configured)",
        value=bool(classifier.gemini_api_key),
        help="Optional: Enables multimodal Gemini analysis for complex math formulas and diagrams."
    )

    if uploaded_file is not None:
        try:
            image_bytes = uploaded_file.getvalue()
            image = Image.open(io.BytesIO(image_bytes))

            col_img, col_info = st.columns([1, 1], gap="medium")

            with col_img:
                st.subheader("Screenshot Preview")
                show_image(image)
                st.caption(f"Dimensions: {image.width}x{image.height} px | Size: {len(image_bytes) / 1024:.1f} KB")

            with col_info:
                st.subheader("🔍 GATE Classification Result")
                with st.spinner("Analyzing screenshot with OCR & GATE syllabus engine..."):
                    analysis = classifier.analyze_image(image, use_ai=use_gemini)

                predicted_subject = analysis.get("subject_id", "General_Notes")
                confidence = float(analysis.get("confidence", 0.0))
                subtopic = analysis.get("subtopic", "General")
                matched_keywords = analysis.get("matched_keywords", [])
                ocr_text = analysis.get("ocr_text", "")

                # Display detected subject badge
                st.markdown(render_subject_badge(predicted_subject, subtopic), unsafe_allow_html=True)
                
                # Confidence progress
                st.progress(min(confidence / 100.0, 1.0))
                st.caption(f"**Confidence:** {confidence:.1f}% | **Source:** {analysis.get('source', 'rule_engine')}")

                # Matched keywords
                if matched_keywords:
                    st.write("**Detected Concepts & Keywords:**")
                    pills_html = "".join([f'<span class="keyword-pill">{kw}</span>' for kw in matched_keywords[:12]])
                    st.markdown(pills_html, unsafe_allow_html=True)

                # Extracted OCR text expander
                with st.expander("📝 Extracted OCR Text", expanded=False):
                    st.text_area("Raw Text", value=ocr_text, height=120, disabled=True, label_visibility="collapsed")

            # Form to confirm / customize and save
            st.divider()
            st.subheader("💾 Review & Save into Subject Folder")

            with st.form("save_screenshot_form"):
                f_col1, f_col2 = st.columns(2)
                with f_col1:
                    # Preselect detected subject
                    default_idx = SUBJECT_KEYS.index(predicted_subject) if predicted_subject in SUBJECT_KEYS else 0
                    selected_subject = st.selectbox(
                        "Target GATE CSE Subject",
                        options=SUBJECT_KEYS,
                        index=default_idx,
                        format_func=lambda k: f"[{SUBJECT_CODES.get(k, '')}] {SUBJECT_NAMES.get(k, k)}"
                    )
                    custom_subtopic = st.text_input("Subtopic / Concept", value=subtopic)

                with f_col2:
                    custom_tags = st.text_input(
                        "Tags (comma separated)",
                        placeholder="PYQ2024, TestSeries, Formula, Hard",
                        value=""
                    )
                    notes = st.text_area(
                        "Personal Notes / Formula / Doubt Explanation",
                        placeholder="Add solution steps, shortcuts, or formula hints here...",
                        height=70
                    )

                submitted = st.form_submit_button("📁 Save Screenshot to Folder", use_container_width=True, type="primary")

                if submitted:
                    tags_list = [t.strip() for t in custom_tags.split(",") if t.strip()]
                    saved_item = storage.save_screenshot(
                        image_bytes=image_bytes,
                        subject_id=selected_subject,
                        subtopic=custom_subtopic.strip() or "General",
                        ocr_text=ocr_text,
                        confidence=confidence,
                        tags=tags_list,
                        notes=notes
                    )
                    st.success(f"✅ Successfully saved to: `{saved_item.get('relative_path')}`")
                    st.balloons()

        except Exception as e:
            st.error(f"Error processing image: {str(e)}")


# ---------------------------------------------------------
# View 2: Notes Library & Search
# ---------------------------------------------------------
def render_library_page():
    st.header("📚 GATE CSE Notes Library & Search")
    st.markdown("Search through all your saved screenshots using extracted OCR text, subject, or tags.")

    # Search and Filter Bar
    filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 1])

    with filter_col1:
        subject_filter_options = ["All Subjects"] + SUBJECT_KEYS
        selected_filter = st.selectbox(
            "Filter by Subject",
            options=subject_filter_options,
            format_func=lambda k: "All Subjects" if k == "All Subjects" else f"[{SUBJECT_CODES.get(k, '')}] {SUBJECT_NAMES.get(k, k)}"
        )
        filter_sub = None if selected_filter == "All Subjects" else selected_filter

    with filter_col2:
        search_query = st.text_input("🔍 Full-Text OCR Search", placeholder="e.g. Banker's, Dijkstra, Eigenvalues, DFA, TCP")

    with filter_col3:
        tag_query = st.text_input("🏷️ Filter by Tag", placeholder="e.g. PYQ2024")

    # Fetch matching screenshots
    res = storage.list_screenshots(
        subject_id=filter_sub,
        search_query=search_query if search_query.strip() else None,
        tag=tag_query if tag_query.strip() else None,
        limit=150
    )

    items = res.get("items", [])
    total = res.get("total", 0)

    # Export to ZIP Action
    st.divider()
    top_bar_col1, top_bar_col2 = st.columns([3, 1])
    with top_bar_col1:
        st.write(f"**Found {total} screenshot(s)** matching criteria:")
    with top_bar_col2:
        try:
            zip_bytes = storage.export_as_zip(subject_id=filter_sub)
            zip_filename = f"gate_cse_{filter_sub or 'all'}_notes.zip"
            st.download_button(
                label="📦 Download Notes (ZIP)",
                data=zip_bytes,
                file_name=zip_filename,
                mime="application/zip",
                use_container_width=True
            )
        except Exception:
            pass

    if not items:
        st.info("No screenshots found. Upload screenshots in the 'Upload & Classify' tab to get started!")
        return

    # Display items in responsive cards
    for idx, item in enumerate(items):
        file_id = item.get("id")
        rel_path = item.get("relative_path")
        abs_path = storage.base_dir / rel_path

        with st.container():
            st.markdown("---")
            card_col1, card_col2 = st.columns([1, 2], gap="medium")

            with card_col1:
                if abs_path.exists():
                    show_image(str(abs_path))
                else:
                    st.warning("Image file missing on disk.")

            with card_col2:
                # Subject badge & subtopic
                st.markdown(
                    render_subject_badge(item.get("subject_id", "General_Notes"), item.get("subtopic", "")),
                    unsafe_allow_html=True
                )
                st.caption(f"📅 Added: {item.get('created_at', '')[:19]} | Size: {item.get('file_size', 0) / 1024:.1f} KB")

                # Notes and Tags
                if item.get("notes"):
                    st.info(f"💡 **Notes:** {item.get('notes')}")

                tags = item.get("tags", [])
                if tags:
                    tags_html = "".join([f'<span class="keyword-pill">#{t}</span>' for t in tags])
                    st.markdown(f"**Tags:** {tags_html}", unsafe_allow_html=True)

                # OCR Text expander
                ocr_text = item.get("ocr_text", "")
                if ocr_text:
                    with st.expander("📄 Extracted Text (OCR)"):
                        st.code(ocr_text, language="text")

                # Actions: Move, Delete, Download
                act_col1, act_col2, act_col3 = st.columns([2, 1, 1])
                with act_col1:
                    new_sub = st.selectbox(
                        "Move to Subject",
                        options=SUBJECT_KEYS,
                        index=SUBJECT_KEYS.index(item.get("subject_id", "General_Notes")) if item.get("subject_id") in SUBJECT_KEYS else 0,
                        key=f"move_sel_{idx}",
                        format_func=lambda k: f"[{SUBJECT_CODES.get(k, '')}] {SUBJECT_NAMES.get(k, k)}"
                    )
                    if st.button("Move Folder", key=f"btn_move_{idx}"):
                        moved = storage.move_screenshot(file_id, new_sub)
                        if moved:
                            st.success(f"Moved to {SUBJECT_NAMES.get(new_sub)}!")
                            safe_rerun()

                with act_col2:
                    st.write("")
                    st.write("")
                    if st.button("🗑️ Delete", key=f"btn_del_{idx}", type="secondary"):
                        storage.delete_screenshot(file_id)
                        st.warning("Screenshot deleted.")
                        safe_rerun()

                with act_col3:
                    st.write("")
                    st.write("")
                    if abs_path.exists():
                        with open(abs_path, "rb") as f_img:
                            st.download_button(
                                "💾 Download",
                                data=f_img.read(),
                                file_name=item.get("filename", "screenshot.png"),
                                mime="image/png",
                                key=f"dl_{idx}"
                            )
                        st.rerun()


# ---------------------------------------------------------
# View 3: Preparation Dashboard
# ---------------------------------------------------------
def render_stats_page(stats):
    st.header("📊 GATE CSE Preparation Dashboard")
    st.markdown("Track your saved screenshots, formula sheets, and doubt distribution across all GATE subjects.")

    total_notes = sum(s["count"] for s in stats)
    total_size_mb = sum(s["total_size"] for s in stats) / (1024 * 1024)
    active_subjects = sum(1 for s in stats if s["count"] > 0)

    # Top metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Screenshots Saved", f"{total_notes}")
    m2.metric("Storage Used", f"{total_size_mb:.2f} MB")
    m3.metric("Subjects Active", f"{active_subjects} / 12")

    st.divider()
    st.subheader("GATE CSE Subject Breakdown")

    # Subject Progress Cards
    for s in stats:
        sub_id = s["subject_id"]
        count = s["count"]
        size_kb = s["total_size"] / 1024
        percentage = (count / total_notes * 100) if total_notes > 0 else 0

        c1, c2, c3 = st.columns([2, 3, 1])
        with c1:
            st.markdown(render_subject_badge(sub_id), unsafe_allow_html=True)
            st.caption(s.get("description", "")[:80] + "...")
        with c2:
            st.progress(min(percentage / 100.0, 1.0))
        with c3:
            st.write(f"**{count}** notes ({size_kb:.1f} KB)")


# ---------------------------------------------------------
# View 4: Settings Page
# ---------------------------------------------------------
def render_settings_page():
    st.header("⚙️ Settings & System Diagnostics")

    # Storage Folder Configuration
    st.subheader("📁 Screenshot Storage Location")
    current_dir = str(storage.base_dir)
    new_dir = st.text_input("Folder Path on Disk", value=current_dir)
    if st.button("Update Storage Folder"):
        if new_dir.strip():
            storage.set_base_dir(new_dir.strip())
            st.success(f"Storage directory updated to: `{new_dir.strip()}`")

    st.divider()

    # Gemini Vision AI
    st.subheader("🤖 Multimodal Gemini Vision AI (Optional)")
    st.markdown(
        "By default, GATE-Snap uses **100% offline local OCR (Tesseract)** with deep GATE keyword pattern matching. "
        "Adding a Gemini API key enables advanced mathematical reasoning and handwritten formula decoding."
    )
    api_key = st.text_input(
        "Google Gemini API Key",
        type="password",
        value=classifier.gemini_api_key or "",
        help="Get a free key from https://aistudio.google.com"
    )
    if st.button("Save Gemini Key"):
        classifier.set_api_key(api_key.strip())
        st.success("Gemini API key updated!")

    st.divider()

    # OCR Diagnostics
    st.subheader("🩺 OCR Engine Diagnostics")
    tess_path = os.popen("which tesseract").read().strip()
    if tess_path:
        st.success(f"✅ Tesseract OCR found at: `{tess_path}`")
        version_out = os.popen("tesseract --version").read().splitlines()
        if version_out:
            st.caption(f"Version: {version_out[0]}")
    else:
        st.error("❌ Tesseract OCR not found. Please install `tesseract-ocr` using your package manager.")


if __name__ == "__main__":
    main()
