"""
FastAPI Server for GATE CSE Screenshot Organizer.
Provides REST APIs and serves interactive web application.
"""

import os
import io
import base64
import subprocess
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query, Response
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from PIL import Image

from classifier import GATEClassifier, GATE_SUBJECTS
from storage import GATEStorage, DEFAULT_BASE_DIR

app = FastAPI(title="GATE CSE Screenshot Organizer")

# Initialize modules
classifier = GATEClassifier()
storage = GATEStorage()

# Mount static files
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

class AnalyzePayload(BaseModel):
    image_base64: str
    use_ai: bool = True

class SavePayload(BaseModel):
    image_base64: str
    subject_id: str
    subtopic: str = "General"
    ocr_text: str = ""
    confidence: float = 0.0
    tags: List[str] = []
    notes: str = ""
    custom_filename: Optional[str] = None

class MovePayload(BaseModel):
    file_id: str
    new_subject_id: str

class SettingsPayload(BaseModel):
    base_dir: Optional[str] = None
    gemini_api_key: Optional[str] = None

def decode_image_base64(data_uri_or_base64: str) -> bytes:
    """Extract raw bytes from data URI or pure base64 string."""
    if "," in data_uri_or_base64:
        data_uri_or_base64 = data_uri_or_base64.split(",", 1)[1]
    return base64.b64decode(data_uri_or_base64)


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>GATE CSE Screenshot Organizer is loading...</h1>")


@app.post("/api/analyze")
async def analyze_screenshot(payload: AnalyzePayload):
    """Analyze a pasted screenshot (Base64), extract OCR, and classify into GATE CSE subject."""
    try:
        image_bytes = decode_image_base64(payload.image_base64)
        image = Image.open(io.BytesIO(image_bytes))
        result = classifier.analyze_image(image, use_ai=payload.use_ai)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"Failed to analyze image: {str(e)}"})


@app.post("/api/save")
async def save_screenshot(payload: SavePayload):
    """Save analyzed screenshot into corresponding GATE CSE subject folder."""
    try:
        image_bytes = decode_image_base64(payload.image_base64)
        meta = storage.save_screenshot(
            image_bytes=image_bytes,
            subject_id=payload.subject_id,
            subtopic=payload.subtopic,
            ocr_text=payload.ocr_text,
            confidence=payload.confidence,
            tags=payload.tags,
            notes=payload.notes,
            custom_filename=payload.custom_filename
        )
        return JSONResponse(content={"success": True, "item": meta})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Failed to save screenshot: {str(e)}"})


@app.post("/api/analyze-and-save")
async def analyze_and_save(payload: AnalyzePayload):
    """Auto-detect subject and instantly save screenshot in 1 step."""
    try:
        image_bytes = decode_image_base64(payload.image_base64)
        image = Image.open(io.BytesIO(image_bytes))
        analysis = classifier.analyze_image(image, use_ai=payload.use_ai)
        
        subject_id = analysis.get("subject_id", "General_Notes")
        subtopic = analysis.get("subtopic", "General")
        ocr_text = analysis.get("ocr_text", "")
        confidence = analysis.get("confidence", 0.0)

        meta = storage.save_screenshot(
            image_bytes=image_bytes,
            subject_id=subject_id,
            subtopic=subtopic,
            ocr_text=ocr_text,
            confidence=confidence,
            tags=["auto-categorized"]
        )
        return JSONResponse(content={"success": True, "analysis": analysis, "item": meta})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Auto-save failed: {str(e)}"})


@app.get("/api/subjects")
async def get_subjects():
    """Get list of GATE CSE subjects with screenshot count and stats."""
    stats = storage.get_subject_statistics()
    return JSONResponse(content={"subjects": stats, "base_dir": str(storage.base_dir)})


@app.get("/api/screenshots")
async def get_screenshots(
    subject_id: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    limit: int = Query(100),
    offset: int = Query(0)
):
    """List screenshots with optional subject, tag, or OCR text search."""
    results = storage.list_screenshots(
        subject_id=subject_id,
        search_query=q,
        tag=tag,
        limit=limit,
        offset=offset
    )
    return JSONResponse(content=results)


@app.get("/api/screenshot-file")
async def get_screenshot_file(path: str = Query(...)):
    """Serve the image file."""
    # Prevent directory traversal
    resolved_path = (storage.base_dir / path).resolve()
    if not str(resolved_path).startswith(str(storage.base_dir)):
        raise HTTPException(status_code=403, detail="Access denied")
    if not resolved_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(resolved_path), media_type="image/png")


@app.post("/api/move")
async def move_screenshot(payload: MovePayload):
    """Move screenshot to another subject folder."""
    result = storage.move_screenshot(payload.file_id, payload.new_subject_id)
    if result:
        return JSONResponse(content={"success": True, "item": result})
    return JSONResponse(status_code=404, content={"error": "Screenshot not found or could not be moved"})


@app.delete("/api/screenshot")
async def delete_screenshot(file_id: str = Query(...)):
    """Delete a screenshot."""
    deleted = storage.delete_screenshot(file_id)
    return JSONResponse(content={"success": deleted})


@app.get("/api/export-zip")
async def export_zip(subject_id: Optional[str] = Query(None)):
    """Download screenshots as a ZIP file."""
    zip_bytes = storage.export_as_zip(subject_id)
    zip_name = f"gate_cse_{subject_id or 'all_subjects'}_notes.zip"
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={zip_name}"}
    )


@app.get("/api/settings")
async def get_settings():
    return JSONResponse(content={
        "base_dir": str(storage.base_dir),
        "has_gemini_key": bool(classifier.gemini_api_key)
    })


@app.post("/api/settings")
async def update_settings(payload: SettingsPayload):
    if payload.base_dir:
        storage.set_base_dir(payload.base_dir)
    if payload.gemini_api_key is not None:
        classifier.set_api_key(payload.gemini_api_key)
    return JSONResponse(content={
        "success": True,
        "base_dir": str(storage.base_dir),
        "has_gemini_key": bool(classifier.gemini_api_key)
    })


@app.post("/api/open-folder")
async def open_folder(subject_id: Optional[str] = Query(None)):
    """Open folder in native desktop file manager (Linux / Ubuntu)."""
    target = storage.base_dir / (subject_id if subject_id else "")
    try:
        if os.name == 'posix':
            subprocess.Popen(["xdg-open", str(target)])
            return JSONResponse(content={"success": True, "path": str(target)})
    except Exception as e:
        pass
    return JSONResponse(content={"success": False, "path": str(target)})


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
