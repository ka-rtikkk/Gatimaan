"""Auth API router"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.auth import authenticate_user, create_access_token, DEMO_USERS

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/login")
async def login(request: LoginRequest) -> LoginResponse:
    user = authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token_data = {"sub": user["username"], "role": user["role"]}
    token = create_access_token(token_data)

    return LoginResponse(
        access_token=token,
        user={
            "username": user["username"],
            "name": user["name"],
            "role": user["role"],
            "department": user["department"],
        },
    )


@router.get("/demo-credentials")
async def demo_credentials():
    """Return demo user credentials for prototype testing"""
    return {
        "note": "PROTOTYPE DEMO CREDENTIALS",
        "users": [
            {"username": "demo", "password": "demo", "role": "Admin (Full Access)"},
            {"username": "admin", "password": "admin123", "role": "Admin"},
            {"username": "control", "password": "control123", "role": "Control Office"},
            {"username": "engineer", "password": "eng123", "role": "Engineering"},
            {"username": "signal", "password": "signal123", "role": "S&T"},
            {"username": "traction", "password": "traction123", "role": "Traction Distribution"},
        ],
    }
