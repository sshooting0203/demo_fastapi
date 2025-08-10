from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from app.models.user import User
from app.services.home_service import home_service
from app.services.ranking_service import RankingService
from app.services.user_service import get_current_user

router = APIRouter(prefix="/api/home", tags=["홈"])
ranking_service = RankingService()

@router.get("/")
async def get_home_data(current_user: dict = Depends(get_current_user)):
    """
    홈 화면 데이터 (MVP: 사용자 정보 + 여행국가 Top 3 음식)
    """
    try:
        uid = current_user["uid"]
        
        # 1. 사용자 기본 정보
        user_info = {
            "uid": uid,
            "displayName": current_user.get("displayName", "사용자"),
            "email": current_user.get("email", ""),
            "currentCountry": None  # 나중에 사용자 프로필에서 가져올 예정
        }
        
        # 2. 여행국가 기반 Top 3 음식
        country_rankings = []
        country_message = None
        
        # 사용자의 여행국가 정보 가져오기
        travel_country_info = home_service.get_travel_country_info(uid)
        
        if travel_country_info:
            user_info["currentCountry"] = travel_country_info["countryCode"]
            # 여행국가가 설정된 경우 상위 3개 음식 조회
            top_foods = await ranking_service.get_top_foods(travel_country_info["countryCode"], 3)
            country_rankings = top_foods
        else:
            # 여행국가 미설정 시 안내 메시지
            country_message = "여행 국가를 설정하면 해당 국가의 인기 음식을 볼 수 있습니다."
        
        return {
            "success": True,
            "user": user_info,
            "countryRankings": country_rankings,
            "countryMessage": country_message
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"홈 데이터 조회 실패: {str(e)}")

@router.post("/register-country")
async def register_travel_country(
    country_name: str,
    current_user: dict = Depends(get_current_user)
):
    """
    여행 국가 등록 (MVP: 등록 시 Top 3 음식 자동 갱신)
    """
    try:
        uid = current_user["uid"]
        result = home_service.register_travel_country(uid, country_name)
        return {
            "success": True,
            "message": "여행 국가가 등록되었습니다.",
            "countryInfo": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"여행 국가 등록 실패: {str(e)}")


