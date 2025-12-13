"""

main.py

========================================

Cardiology AI Backend Server with CORS Support

Serves HTML files, static files, and handles API requests

========================================

"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import shutil
from pathlib import Path
from typing import Optional

# Import custom modules
from imaging import process_nifti
from ai_engine import run_ai_analysis

# Initialize FastAPI app
app = FastAPI(
    title="Cardiology AI Backend",
    description="Backend API for AI-powered cardiac disease detection",
    version="1.0.0",
)

# =========================================================
# CORS MIDDLEWARE - ALLOWS REQUESTS FROM ANY ORIGIN
# =========================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (frontend)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# DIRECTORY SETUP
# =========================================================
BASE_DIR = Path(__file__).parent.absolute()
UPLOAD_DIR = BASE_DIR / "uploads"
SLICES_DIR = BASE_DIR / "slices"
UPLOAD_DIR.mkdir(exist_ok=True)
SLICES_DIR.mkdir(exist_ok=True)

print(f"📁 Base directory: {BASE_DIR}")
print(f"📁 Upload directory: {UPLOAD_DIR}")
print(f"📁 Slices directory: {SLICES_DIR}")

# =========================================================
# MOUNT STATIC FILES (for images, slices, etc.)
# =========================================================
# Serve slices directory under /slices
app.mount("/slices", StaticFiles(directory=str(SLICES_DIR)), name="slices")

# =========================================================
# SERVE HTML FILES (MUST BE BEFORE CATCH-ALL ROUTES)
# =========================================================
@app.get("/")
async def serve_home():
    """Serve analyze.html as homepage"""
    html_path = BASE_DIR / "analyze.html"
    if html_path.exists():
        return FileResponse(str(html_path))
    return {"error": "analyze.html not found", "path": str(html_path)}

@app.get("/analyze")
@app.get("/analyze.html")
async def serve_analyze():
    """Serve analyze.html"""
    html_path = BASE_DIR / "analyze.html"
    if html_path.exists():
        return FileResponse(str(html_path))
    raise HTTPException(status_code=404, detail="analyze.html not found")

@app.get("/result")
async def serve_result_root():
    """Serve result.html when /result is requested"""
    html_path = BASE_DIR / "result.html"
    if html_path.exists():
        return FileResponse(str(html_path))
    raise HTTPException(status_code=404, detail="result.html not found")

@app.get("/result.html")
async def serve_result_html():
    """Serve result.html explicitly"""
    html_path = BASE_DIR / "result.html"
    if html_path.exists():
        return FileResponse(str(html_path))
    raise HTTPException(status_code=404, detail="result.html not found")

@app.get("/heart")
@app.get("/heart.html")
async def serve_heart():
    """Serve heart.html if it exists, otherwise suggest analyze"""
    html_path = BASE_DIR / "heart.html"
    if html_path.exists():
        return FileResponse(str(html_path))
    return {"message": "heart.html not found", "redirect": "Use / or /analyze instead"}

# =========================================================
# SERVE STATIC IMAGE FILES (AFTER HTML ROUTES)
# =========================================================
@app.get("/image.jpg")
async def serve_emblem():
    """Serve the government emblem image"""
    image_path = BASE_DIR / "image.jpg"
    if image_path.exists():
        return FileResponse(str(image_path))
    raise HTTPException(status_code=404, detail="image.jpg not found")

# =========================================================
# MAIN ANALYSIS ENDPOINT
# =========================================================
@app.post("/api/analyze-heart")
async def analyze_heart(
    ct_mri_file: UploadFile = File(...),
    patient_name: str = Form(...),
    patient_age: int = Form(...),
    patient_sex: str = Form(...),
    patient_notes: Optional[str] = Form(""),
    ecg_file: Optional[UploadFile] = File(None),
    blood_test_file: Optional[UploadFile] = File(None),
    echo_file: Optional[UploadFile] = File(None),
):
    """
    Main endpoint for cardiac AI analysis.
    Processes medical imaging and generates AI-powered disease detection report.
    """
    print("=" * 60)
    print("🫀 NEW ANALYSIS REQUEST RECEIVED")
    print("=" * 60)
    print(f"📋 Patient: {patient_name}, Age: {patient_age}, Sex: {patient_sex}")
    print(f"📁 CT/MRI File: {ct_mri_file.filename}")
    
    if ecg_file:
        print(f"📈 ECG File: {ecg_file.filename}")
    if blood_test_file:
        print(f"🩸 Blood Test: {blood_test_file.filename}")
    if echo_file:
        print(f"🔊 ECHO File: {echo_file.filename}")
    
    try:
        # =====================================================
        # SAVE UPLOADED FILES
        # =====================================================
        # Save CT/MRI scan (mandatory)
        ct_path = UPLOAD_DIR / ct_mri_file.filename
        with open(ct_path, "wb") as f:
            content = await ct_mri_file.read()
            f.write(content)
        print(f"✅ Saved CT/MRI to: {ct_path}")
        
        # Save optional files
        if ecg_file:
            ecg_path = UPLOAD_DIR / ecg_file.filename
            with open(ecg_path, "wb") as f:
                content = await ecg_file.read()
                f.write(content)
            print(f"✅ Saved ECG: {ecg_file.filename}")
        
        if blood_test_file:
            blood_path = UPLOAD_DIR / blood_test_file.filename
            with open(blood_path, "wb") as f:
                content = await blood_test_file.read()
                f.write(content)
            print(f"✅ Saved Blood Test: {blood_test_file.filename}")
        
        if echo_file:
            echo_path = UPLOAD_DIR / echo_file.filename
            with open(echo_path, "wb") as f:
                content = await echo_file.read()
                f.write(content)
            print(f"✅ Saved ECHO: {echo_file.filename}")
        
        # =====================================================
        # PROCESS CT/MRI WITH HEART SEGMENTATION
        # =====================================================
        print("🔄 Processing NIfTI file with heart segmentation...")
        import time
        start_time = time.time()
        
        meta, resolution, measurements, slices_data, sliders = process_nifti(str(ct_path))
        
        elapsed = time.time() - start_time
        print(f"✅ NIfTI processing complete ({elapsed:.2f}s)")
        print(f"   Shape: {resolution['image_size']}")
        print(f"   Slices: {resolution['num_slices']}")
        
        # =====================================================
        # RUN AI ANALYSIS
        # =====================================================
        print("🤖 Running AI disease detection analysis...")
        ai_start = time.time()
        
        ai_summary, diseases, label_stats, preview3d = run_ai_analysis()
        
        ai_result = {
            "finding": ai_summary["label"],
            "confidence_score": f"{int(ai_summary['confidence'] * 100)}%",
            "explanation": ai_summary["explanation"],
            "diseases": diseases,
            "label_stats": label_stats,
        }
        
        ai_elapsed = time.time() - ai_start
        print(f"✅ AI analysis complete ({ai_elapsed:.2f}s)")
        print(f"   Finding: {ai_result['finding']}")
        print(f"   Confidence: {ai_result['confidence_score']}")
        
        # =====================================================
        # PREPARE RESPONSE
        # =====================================================
        response_data = {
            "status": "success",
            "patient_info": {
                "name": patient_name,
                "age": patient_age,
                "sex": patient_sex,
                "notes": patient_notes,
            },
            "scan_metadata": meta,
            "resolution": resolution,
            "measurements": measurements,
            "slices": slices_data,
            "sliders": sliders,
            "ai_analysis": ai_result,
        }
        
        total_time = time.time() - start_time
        print("=" * 60)
        print(f"✅ ANALYSIS COMPLETE - Total time: {total_time:.2f}s")
        print("=" * 60)
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        print("=" * 60)
        print("❌ ERROR OCCURRED")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# =========================================================
# CLEAR DATA ENDPOINT
# =========================================================
@app.post("/api/clear-data")
async def clear_data():
    """
    Clear all uploaded files and generated slices.
    This endpoint is called when user clicks 'Clear All Data' button.
    """
    print("=" * 60)
    print("🗑️  CLEARING ALL DATA")
    print("=" * 60)
    
    try:
        # Clear uploads directory
        if UPLOAD_DIR.exists():
            for file in UPLOAD_DIR.glob("*"):
                if file.is_file():
                    file.unlink()
                    print(f"   Deleted: {file.name}")
        
        # Clear slices directory
        if SLICES_DIR.exists():
            for file in SLICES_DIR.glob("*"):
                if file.is_file():
                    file.unlink()
                    print(f"   Deleted: {file.name}")
        
        print("✅ All data cleared successfully")
        print("=" * 60)
        
        return JSONResponse(
            content={"status": "success", "message": "All data cleared successfully"}
        )
        
    except Exception as e:
        print(f"❌ Error clearing data: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# =========================================================
# HEALTH CHECK
# =========================================================
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Cardiology AI Backend"}

# =========================================================
# CATCH-ALL ROUTE FOR STATIC FILES (MUST BE LAST!)
# =========================================================
@app.get("/{filename}")
async def serve_static_file(filename: str):
    """Serve any static image file from base directory"""
    allowed_extensions = [".jpg", ".jpeg", ".png", ".gif", ".svg", ".ico"]
    file_path = BASE_DIR / filename
    
    if file_path.exists() and file_path.suffix.lower() in allowed_extensions:
        return FileResponse(str(file_path))
    
    # Not a static image, return 404
    raise HTTPException(status_code=404, detail=f"{filename} not found")

# =========================================================
# RUN SERVER
# =========================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🫀 Starting Cardiology AI Backend Server...")
    print("=" * 60)
    print("📡 Access at: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🌐 Analysis Page: http://localhost:8000")
    print("📊 Results Page: http://localhost:8000/result.html")
    print()
    print("✅ CORS enabled - accepts requests from any origin")
    print("✅ Static file serving enabled")
    print("=" * 60)
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
