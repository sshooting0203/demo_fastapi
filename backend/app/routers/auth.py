from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from ..models.user import User
from ..services.user_service import user_service, get_current_user
import logging
from typing import Dict

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["인증"])

# HTTP Bearer 인증을 위한 의존성
# 일단 여긴 playground - oauth 클라이언트 생성해서 테스트하니 통과 -> 근데 연결해봐야 또 알 듯
security = HTTPBearer()

@router.post("/login")
async def login_with_firebase_token(
    current_user: Dict = Depends(get_current_user),   # ✅ 의존성으로 바로 받기
):
    user = await user_service.create_or_update_user(current_user)
    return {
        "success": True,
        "message": "로그인 성공",
        "user": {
            "uid": user.uid,
            "displayName": user.displayName,
            "email": user.email,
            "currentCountry": user.currentCountry,
        },
    }

@router.get("/me")
async def get_current_user_info(
    current_user: Dict = Depends(get_current_user), 
):
    uid = current_user["uid"]
    user = await user_service.get_user_profile(uid)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return {
        "success": True,
        "user": {
            "uid": user.uid,
            "displayName": user.displayName,
            "email": user.email,
            "currentCountry": user.currentCountry,
        },
    }