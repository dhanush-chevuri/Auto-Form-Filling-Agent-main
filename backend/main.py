from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import httpx
import os
from pathlib import Path
from dotenv import load_dotenv
from .services.resume_parser import ResumeParser
from .services.form_analyzer import FormAnalyzer
from .services.form_filler import FormFiller
from .services.google_forms_service import GoogleFormsService
from .logger import log_request, log_response, log_error
import traceback

load_dotenv()

app = FastAPI(title="Auto Form Filling Agent", version="1.0.0")

# Add CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Serve frontend static files if build exists
frontend_build_path = Path(__file__).parent.parent / "frontend" / "build"
if frontend_build_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_build_path / "static")), name="static")

class FormFillRequest(BaseModel):
    form_url: str

@app.post("/api/parse-resume")
async def parse_resume(file: UploadFile = File(...)):
    # Avoid accessing UploadFile.size (not provided); log filename only
    log_request("/api/parse-resume", {"filename": file.filename})
    try:
        if not file.filename.endswith(('.pdf', '.docx', '.txt')):
            log_error(f"Unsupported file format: {file.filename}", "parse-resume")
            raise HTTPException(status_code=400, detail="Unsupported file format")

        parser = ResumeParser()
        content = await file.read()
        extracted_data = await parser.extract_data(content, file.filename)

        # Check if PDF is ATS-friendly
        if not extracted_data.get('ats_friendly', True):
            response = {
                "success": False,
                "ats_friendly": False,
                "error": extracted_data.get('error', 'PDF is not ATS-friendly'),
                "message": extracted_data.get('message', ''),
                "suggestions": extracted_data.get('suggestions', [])
            }
            log_response("/api/parse-resume", response)
            return response

        response = {"success": True, "ats_friendly": True, "data": extracted_data}
        log_response("/api/parse-resume", response)
        return response
    except Exception as e:
        tb = traceback.format_exc()
        log_error(f"{str(e)}\n{tb}", "parse-resume")
        # Return structured error so frontend gets JSON instead of an HTTP 500
        return {"success": False, "error": str(e)}

@app.post("/api/analyze-form")
async def analyze_form(request: FormFillRequest):
    log_request("/api/analyze-form", {"form_url": request.form_url})
    try:
        # Use Google Forms service instead of Selenium
        google_forms = GoogleFormsService()
        form_structure = await google_forms.get_form_structure(request.form_url)

        response = {"success": True, "fields": form_structure["fields"], "form_id": form_structure["form_id"]}
        log_response("/api/analyze-form", response)
        return response
    except Exception as e:
        tb = traceback.format_exc()
        log_error(f"{str(e)}\n{tb}", "analyze-form")
        return {"success": False, "error": str(e)}

@app.post("/api/fill-form")
async def fill_form(
    form_url: str = Form(...),
    file: UploadFile = File(...)
):
    log_request("/api/fill-form", {"form_url": form_url, "filename": file.filename})
    
    try:
        parser = ResumeParser()
        google_forms = GoogleFormsService()
        
        # Parse resume
        content = await file.read()
        resume_data = await parser.extract_data(content, file.filename)
        
        # Check if PDF is ATS-friendly
        if not resume_data.get('ats_friendly', True):
            result = {
                "success": False,
                "ats_friendly": False,
                "error": resume_data.get('error', 'PDF is not ATS-friendly'),
                "message": resume_data.get('message', 'Cannot fill form with non-ATS-friendly PDF'),
                "suggestions": resume_data.get('suggestions', [])
            }
            log_response("/api/fill-form", result)
            return result
        
        # Submit form directly using Google Forms API
        result = await google_forms.submit_form_response(form_url, resume_data)
        
        log_response("/api/fill-form", result)
        return result
    except Exception as e:
        tb = traceback.format_exc()
        log_error(f"{str(e)}\n{tb}", "fill-form")
        return {"success": False, "error": str(e)}

@app.get("/api/hello")
async def hello_world():
    return {"message": "Hello World!"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

# Serve frontend index.html for all non-API routes (SPA support)
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """Serve React frontend for all routes except /api"""
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    index_file = frontend_build_path / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    
    # If frontend not built, return API-only message
    return {"message": "API is running. Frontend not built yet.", "endpoints": ["/api/health", "/api/parse-resume", "/api/fill-form"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)