from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from ..services.home_service import home_service
from ..services.user_service import get_current_user

router = APIRouter(prefix="/api/home", tags=["홈"])

@router.get("")
async def get_home_data(current_user: dict = Depends(get_current_user)):
    """홈 화면 데이터: 사용자 요약 + 현재 국가 Top3"""
    try:
        uid = current_user["uid"]
        
        # 기본 사용자 정보 구성
        user_info = {
            "uid": uid,
            "displayName": current_user.get("displayName", "사용자"),
            "email": current_user.get("email", ""),
            "currentCountry": None
        }

        # 홈 서비스에서 통합 데이터 조회
        home_data = await home_service.get_home_data(uid, user_info)
        return {"success": True, **home_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"홈 데이터 조회 실패: {str(e)}")