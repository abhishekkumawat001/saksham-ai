from fastapi import APIRouter
router = APIRouter()

@router.post("/request-otp")
def request_otp(phone_number: str):
    return {"message": "OTP sent"}

@router.post("/verify-otp")
def verify_otp(phone_number: str, otp: str):
    return {"token": "jwt_token_here"}
