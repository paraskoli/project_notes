"""
Storage manager for GATE CSE screenshots.
Organizes screenshots into subject-specific directories and maintains metadata.
"""

import os
import io
import json
import time
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from PIL import Image
from classifier import GATE_SUBJECTS

DEFAULT_BASE_DIR = os.path.expanduser("~/gate_cse_notes")

class GATEStorage:
    def __init__(self, base_dir: str = DEFAULT_BASE_DIR):
        self.base_dir = Path(base_dir).resolve()
        self.metadata_file = self.base_dir / ".metadata.json"
        self.init_directories()

    def set_base_dir(self, new_path: str):
        self.base_dir = Path(os.path.expanduser(new_path)).resolve()
        self.metadata_file = self.base_dir / ".metadata.json"
        self.init_directories()

    def init_directories(self):
        """Create base directory and subject folders."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        for subject_key in GATE_SUBJECTS.keys():
            (self.base_dir / subject_key).mkdir(parents=True, exist_ok=True)
        (self.base_dir / "General_Notes").mkdir(parents=True, exist_ok=True)
        
        if not self.metadata_file.exists():
            self._save_all_metadata({})

    def _load_all_metadata(self) -> Dict[str, Any]:
        if not self.metadata_file.exists():
            return {}
        try:
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_all_metadata(self, data: Dict[str, Any]):
        try:
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to write metadata: {e}")

    def save_screenshot(
        self,
        image_bytes: bytes,
        subject_id: str,
        subtopic: str = "general",
        ocr_text: str = "",
        confidence: float = 0.0,
        tags: Optional[List[str]] = None,
        notes: str = "",
        custom_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """Save screenshot image into the designated subject folder with metadata."""
        folder_name = subject_id if subject_id in GATE_SUBJECTS or subject_id == "General_Notes" else "General_Notes"
        target_dir = self.base_dir / folder_name
        target_dir.mkdir(parents=True, exist_ok=True)

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug_subtopic = "".join(c if c.isalnum() else "_" for c in subtopic).strip("_").lower()[:20] or "note"

        code = GATE_SUBJECTS.get(folder_name, {}).get("code", "NOTE")
        
        if custom_filename and custom_filename.strip():
            filename = custom_filename.strip()
            if not filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                filename += ".png"
        else:
            filename = f"{code}_{timestamp_str}_{slug_subtopic}.png"

        target_path = target_dir / filename
        
        # Avoid collisions if file already exists
        counter = 1
        base_stem = target_path.stem
        while target_path.exists():
            filename = f"{base_stem}_{counter}.png"
            target_path = target_dir / filename
            counter += 1

        # Save image
        image = Image.open(io.BytesIO(image_bytes))
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        image.save(target_path, "PNG", optimize=True)

        file_id = f"{folder_name}/{filename}"
        file_size = target_path.stat().st_size

        meta_entry = {
            "id": file_id,
            "filename": filename,
            "subject_id": folder_name,
            "subject_name": GATE_SUBJECTS.get(folder_name, {}).get("name", "General Notes"),
            "subtopic": subtopic,
            "tags": tags or [],
            "notes": notes,
            "confidence": confidence,
            "ocr_text": ocr_text,
            "file_size": file_size,
            "dimensions": f"{image.width}x{image.height}",
            "created_at": datetime.now().isoformat(),
            "relative_path": str(target_path.relative_to(self.base_dir)),
            "absolute_path": str(target_path)
        }

        # Update metadata storage
        all_meta = self._load_all_metadata()
        all_meta[file_id] = meta_entry
        self._save_all_metadata(all_meta)

        return meta_entry

    def get_subject_statistics(self) -> List[Dict[str, Any]]:
        """Return counts and stats for all GATE CSE subject folders."""
        all_meta = self._load_all_metadata()
        subject_counts: Dict[str, Dict[str, Any]] = {}

        # Prepopulate with standard subjects
        for sub_id, data in GATE_SUBJECTS.items():
            subject_counts[sub_id] = {
                "subject_id": sub_id,
                "name": data["name"],
                "code": data["code"],
                "color": data["color"],
                "icon": data["icon"],
                "description": data["description"],
                "count": 0,
                "total_size": 0,
                "last_added": None
            }
        
        # Also include General_Notes
        subject_counts["General_Notes"] = {
            "subject_id": "General_Notes",
            "name": "General Notes & Tips",
            "code": "GEN",
            "color": "#64748B",
            "icon": "book-outline",
            "description": "General GATE CSE preparation notes, doubt screenshots, and uncategorized tips",
            "count": 0,
            "total_size": 0,
            "last_added": None
        }

        # Count from metadata and verify file exists on disk
        for file_id, meta in all_meta.items():
            sub = meta.get("subject_id", "General_Notes")
            if sub not in subject_counts:
                subject_counts[sub] = {
                    "subject_id": sub,
                    "name": meta.get("subject_name", sub),
                    "code": "SUB",
                    "color": "#6B7280",
                    "icon": "folder-outline",
                    "description": "",
                    "count": 0,
                    "total_size": 0,
                    "last_added": None
                }
            
            file_path = self.base_dir / meta.get("relative_path", "")
            if file_path.exists():
                subject_counts[sub]["count"] += 1
                subject_counts[sub]["total_size"] += file_path.stat().st_size
                created_at = meta.get("created_at")
                if not subject_counts[sub]["last_added"] or (created_at and created_at > subject_counts[sub]["last_added"]):
                    subject_counts[sub]["last_added"] = created_at

        return list(subject_counts.values())

    def list_screenshots(
        self,
        subject_id: Optional[str] = None,
        search_query: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Query and filter stored screenshots."""
        all_meta = self._load_all_metadata()
        items = []

        query = search_query.lower().strip() if search_query else None
        tag_filter = tag.lower().strip() if tag else None

        for file_id, meta in all_meta.items():
            # Check subject filter
            if subject_id and meta.get("subject_id") != subject_id:
                continue

            # Check tag filter
            if tag_filter:
                item_tags = [t.lower() for t in meta.get("tags", [])]
                if tag_filter not in item_tags:
                    continue

            # Check text query (searches in ocr_text, notes, filename, subtopic)
            if query:
                combined_text = f"{meta.get('ocr_text', '')} {meta.get('notes', '')} {meta.get('filename', '')} {meta.get('subtopic', '')}".lower()
                if query not in combined_text:
                    continue

            # Verify file exists on disk
            rel_path = meta.get("relative_path")
            if rel_path and (self.base_dir / rel_path).exists():
                items.append(meta)

        # Sort by creation date descending
        items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        total = len(items)
        paged = items[offset: offset + limit]

        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "items": paged
        }

    def move_screenshot(self, file_id: str, new_subject_id: str) -> Optional[Dict[str, Any]]:
        """Move a screenshot to a different subject folder."""
        all_meta = self._load_all_metadata()
        if file_id not in all_meta:
            return None

        meta = all_meta[file_id]
        old_rel_path = meta.get("relative_path")
        old_path = self.base_dir / old_rel_path
        if not old_path.exists():
            return None

        new_dir = self.base_dir / new_subject_id
        new_dir.mkdir(parents=True, exist_ok=True)

        filename = old_path.name
        new_path = new_dir / filename
        
        # Handle collision if file already exists in target
        counter = 1
        base_stem = old_path.stem
        while new_path.exists():
            filename = f"{base_stem}_{counter}{old_path.suffix}"
            new_path = new_dir / filename
            counter += 1

        shutil.move(str(old_path), str(new_path))

        # Update metadata
        del all_meta[file_id]
        new_file_id = f"{new_subject_id}/{filename}"
        meta["id"] = new_file_id
        meta["filename"] = filename
        meta["subject_id"] = new_subject_id
        meta["subject_name"] = GATE_SUBJECTS.get(new_subject_id, {}).get("name", new_subject_id)
        meta["relative_path"] = str(new_path.relative_to(self.base_dir))
        meta["absolute_path"] = str(new_path)
        all_meta[new_file_id] = meta
        self._save_all_metadata(all_meta)

        return meta

    def delete_screenshot(self, file_id: str) -> bool:
        """Delete screenshot and its metadata."""
        all_meta = self._load_all_metadata()
        if file_id in all_meta:
            meta = all_meta[file_id]
            file_path = self.base_dir / meta.get("relative_path", "")
            if file_path.exists():
                try:
                    file_path.unlink()
                except Exception as e:
                    print(f"Error unlinking file: {e}")
            del all_meta[file_id]
            self._save_all_metadata(all_meta)
            return True
        return False

    def export_as_zip(self, subject_id: Optional[str] = None) -> bytes:
        """Export all or a specific subject folder as a zip archive."""
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            folders_to_zip = [subject_id] if subject_id else [k for k in GATE_SUBJECTS.keys()] + ["General_Notes"]
            for folder in folders_to_zip:
                folder_path = self.base_dir / folder
                if folder_path.exists():
                    for file in folder_path.glob("*.*"):
                        if file.is_file() and not file.name.startswith("."):
                            arcname = f"{folder}/{file.name}"
                            zf.write(file, arcname=arcname)
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
