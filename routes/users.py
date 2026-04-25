# routes/users.py
from fastapi import APIRouter, HTTPException
from models.user import RegisterRequest, LoginRequest, UserResponse
from services import user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register", response_model=UserResponse)
async def register(body: RegisterRequest):
    try:
        data = await user_service.register_user(
            nickname=body.nickname,
            username=body.username,
            password=body.password,
        )
        return UserResponse(success=True, message="Registration successful!", data=data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login", response_model=UserResponse)
async def login(body: LoginRequest):
    try:
        data = await user_service.login_user(
            username=body.username,
            password=body.password,
        )
        return UserResponse(success=True, message="Login successful!", data=data)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return UserResponse(success=True, message="User found.", data=user)