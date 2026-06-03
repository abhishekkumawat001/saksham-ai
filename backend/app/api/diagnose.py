from fastapi import APIRouter, UploadFile, File
router = APIRouter()

@router.post("/image")
def diagnose_image(file: UploadFile = File(...)):
    # Uploads to S3 -> triggers Celery async task running ResNet50
    return {"job_id": "12345", "status": "processing"}

@router.get("/{job_id}")
def check_diagnosis_status(job_id: str):
    return {"disease": "Leaf Curl Virus", "confidence": 0.87, "remedy": [], "products": []}
