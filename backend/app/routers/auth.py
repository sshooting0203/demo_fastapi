# @ Test Complete
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from app.models.user import User
from app.services.user_service import user_service, get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["인증"])

# HTTP Bearer 인증을 위한 의존성
security = HTTPBearer()

@router.post("/login")
async def login_with_firebase_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Firebase ID Token으로 로그인 (MVP: Google OAuth)
    - 프론트에서 Firebase Auth로 로그인 → ID Token 발급
    - 백엔드로 토큰 전송 → 검증 후 유저 정보 Firestore에 생성/갱신
    """
    try:
        # Firebase 토큰 검증 및 사용자 정보 추출
        user_info = await get_current_user(credentials)
        
        # 사용자 정보를 Firestore에 생성/갱신
        user = await user_service.create_or_update_user(user_info)
        
        return {
            "success": True,
            "message": "로그인 성공",
            "user": {
                "uid": user.uid,
                "displayName": user.displayName,
                "email": user.email,
                "currentCountry": user.currentCountry
            }
        }
        
    except Exception as e:
        logger.error(f"로그인 실패: {str(e)}")
        raise HTTPException(status_code=401, detail=f"로그인 실패: {str(e)}")

@router.get("/me")
async def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """현재 로그인한 사용자 정보 조회"""
    try:
        user_info = await get_current_user(credentials)
        uid = user_info["uid"]
        
        user = await user_service.get_user_profile(uid)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        return {
            "success": True,
            "user": {
                "uid": user.uid,
                "displayName": user.displayName,
                "email": user.email,
                "currentCountry": user.currentCountry
            }
        }
        
    except Exception as e:
        logger.error(f"사용자 정보 조회 실패: {str(e)}")
        raise HTTPException(status_code=401, detail=f"사용자 정보 조회 실패: {str(e)}")
