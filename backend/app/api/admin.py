from fastapi import APIRouter
router = APIRouter()
@router.post("/products")
def add_product():
    return {"message": "Product added"}
@router.get("/analytics")
def get_analytics():
    return {"sessions": 100, "active_users": 50}
