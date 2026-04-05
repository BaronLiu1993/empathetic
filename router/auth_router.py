from unittest import result

from fastapi import APIRouter, HTTPException
from schema.auth_schema import RegisterSchema
from service.user_auth import create_user


router = APIRouter(
    prefix="/v1/api/auth",
    tags=["auth"],
)

@router.post("/login")
async def login_endpoint():
    try:
        
        return {"message": "Login endpoint - not implemented"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/register")
async def register_endpoint(req: RegisterSchema):
    try:
        create_user(email=req.email, password=req.password)
        return {"message": "User registered successfully", "user": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))