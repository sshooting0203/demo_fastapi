from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from ..models.user import User
from ..services.user_service import user_service, get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["인증"])

security = HTTPBearer()

@router.get("/me")
async def get_current_user_info(
    current_user: Dict = Depends(get_current_user), 
):
    """토큰 검증 + 유저 upsert + 최소 프로필 반환"""
    uid = current_user["uid"]
    user = await user_service.create_or_update_user(current_user)
    
    return {
        "success": True,
        "user": {
            "uid": user.uid,
            "displayName": user.displayName,
            "email": user.email,
            "currentCountry": user.currentCountry,
        },
    }