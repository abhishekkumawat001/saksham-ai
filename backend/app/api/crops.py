from fastapi import APIRouter
router = APIRouter()

@router.get("/")
def list_crops():
    return []

@router.get("/{crop_id}/advice")
def get_crop_advice(crop_id: str):
    return {"fertilizers": [], "pesticides": [], "seeds": []}
