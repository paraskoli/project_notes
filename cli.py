#!/usr/bin/env python3
"""
Command-Line Interface for GATE CSE Screenshot Organizer.
Allows classifying and sorting screenshots directly from terminal or clipboard.
"""

import sys
import os
import argparse
from pathlib import Path
from PIL import Image, ImageGrab

from classifier import GATEClassifier, GATE_SUBJECTS
from storage import GATEStorage

def main():
    parser = argparse.ArgumentParser(description="GATE CSE Screenshot Classifier & Organizer")
    parser.add_argument("--image", "-i", type=str, help="Path to image file to analyze and organize")
    parser.add_argument("--paste", "-p", action="store_true", help="Grab screenshot directly from system clipboard")
    parser.add_argument("--subtopic", "-s", type=str, default="", help="Optional subtopic override")
    parser.add_argument("--notes", "-n", type=str, default="", help="Optional notes")
    parser.add_argument("--tags", "-t", type=str, default="", help="Comma separated tags")
    parser.add_argument("--dry-run", action="store_true", help="Analyze without saving to disk")
    parser.add_argument("--stats", action="store_true", help="Show GATE CSE subject statistics")
    parser.add_argument("--dir", "-d", type=str, default="", help="Base storage directory")

    args = parser.parse_args()

    storage = GATEStorage(args.dir) if args.dir else GATEStorage()
    classifier = GATEClassifier()

    if args.stats:
        stats = storage.get_subject_statistics()
        print("\n" + "=" * 65)
        print("          GATE CSE SCREENSHOT ORGANIZER - SUBJECT STATS")
        print("=" * 65)
        print(f"{'Code':<6} | {'Subject':<32} | {'Count':<6} | {'Size':<10}")
        print("-" * 65)
        total_count = 0
        total_size = 0
        for s in stats:
            total_count += s["count"]
            total_size += s["total_size"]
            size_kb = s["total_size"] / 1024
            size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.2f} MB"
            print(f"{s['code']:<6} | {s['name']:<32} | {s['count']:<6} | {size_str:<10}")
        print("-" * 65)
        print(f"Total: {total_count} screenshots in {storage.base_dir}\n")
        return

    img = None
    if args.paste:
        print("Grabbing image from clipboard...")
        try:
            img = ImageGrab.grabclipboard()
            if not isinstance(img, Image.Image):
                print("Error: No image found on clipboard! Copy a screenshot first.")
                sys.exit(1)
        except Exception as e:
            print(f"Clipboard error: {e}")
            sys.exit(1)
    elif args.image:
        img_path = Path(args.image)
        if not img_path.exists():
            print(f"Error: File {args.image} does not exist.")
            sys.exit(1)
        img = Image.open(img_path)
    else:
        parser.print_help()
        print("\nTip: To start the web application, run: ./start.sh or python3 app.py")
        sys.exit(0)

    print("\n[+] Analyzing screenshot with OCR and GATE CSE Knowledge Engine...")
    analysis = classifier.analyze_image(img, use_ai=True)

    print("\n" + "-" * 50)
    print(f"Detected Subject : {analysis['subject_name']} ({analysis['subject_code']})")
    print(f"Folder Target    : {storage.base_dir / analysis['folder_name']}")
    print(f"Subtopic         : {analysis.get('subtopic')}")
    print(f"Confidence       : {analysis.get('confidence')}%")
    print(f"Keywords Matched : {', '.join(analysis.get('matched_keywords', [])[:5])}")
    print("-" * 50)

    ocr_sample = analysis.get("ocr_text", "").strip().replace("\n", " ")[:120]
    if ocr_sample:
        print(f"OCR Snippet      : \"{ocr_sample}...\"")

    if args.dry_run:
        print("\n[Dry Run] Image not saved.")
        return

    # Save to storage
    import io
    buf = io.BytesIO()
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    subtopic = args.subtopic or analysis.get("subtopic", "General")
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]

    item = storage.save_screenshot(
        image_bytes=img_bytes,
        subject_id=analysis["folder_name"],
        subtopic=subtopic,
        ocr_text=analysis.get("ocr_text", ""),
        confidence=analysis.get("confidence", 0.0),
        tags=tags,
        notes=args.notes
    )

    print(f"\n[SUCCESS] Screenshot saved to: {item['absolute_path']}\n")

if __name__ == "__main__":
    main()
