from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from ..services.home_service import home_service
from ..services.ranking_service import RankingService
from ..services.user_service import get_current_user

router = APIRouter(prefix="/api/home", tags=["홈"])
ranking_service = RankingService()
class CountryRegisterRequest(BaseModel):
    country_name: Optional[str] = None
    country_code: Optional[str] = None

@router.get("/")
async def get_home_data(current_user: dict = Depends(get_current_user)):
    """
    홈 화면 데이터 (MVP: 사용자 정보 + 여행국가 Top 3 음식)
    """
    try:
        uid = current_user["uid"]

        # 1) 사용자 정보 기본
        user_info = {
            "uid": uid,
            "displayName": current_user.get("displayName", "사용자"),
            "email": current_user.get("email", ""),
            "currentCountry": None
        }

        # 2) 여행국가 기반 Top 3
        top_foods: List[Dict[str, Any]] = []
        travel_country_info = home_service.get_travel_country_info(uid)  # {"countryCode": "JP", ...} 가정

        if travel_country_info and travel_country_info.get("countryCode"):
            country_code = travel_country_info["countryCode"]
            user_info["currentCountry"] = country_code

            # 랭킹 서비스에서 상위 N개 조회
            foods = await ranking_service.get_top_foods(country_code, 3)

            # 스펙의 topFoods 형태에 맞춰 매핑 (이미 맞다면 그대로 반환)
            # 예시 목표 형태: {"id":"JP_tonkatsu","name":"Tonkatsu","names":{"default":"Tonkatsu"},"imageUrl":"..."}
            def normalize(food: Dict[str, Any]) -> Dict[str, Any]:
                return {
                    "id": food.get("id") or food.get("foodId"),
                    "name": food.get("name") or food.get("names", {}).get("default") or food.get("foodName"),
                    "names": food.get("names") or {"default": food.get("name") or food.get("foodName")},
                    "imageUrl": food.get("imageUrl"),
                }
            top_foods = [normalize(f) for f in foods]
        else:
            # 여행국가가 없으면 topFoods는 빈 배열로
            pass

        return {"success": True, "user": user_info, "topFoods": top_foods}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"홈 데이터 조회 실패: {str(e)}")

@router.post("/register-country")
async def register_travel_country(
    req: CountryRegisterRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    여행 국가 등록 (MVP: 등록 시 Top 3 음식 자동 갱신)
    """
    try:
        uid = current_user["uid"]
        if not (req.country_code or req.country_name):
            raise HTTPException(status_code=422, detail="country_name 또는 country_code 중 하나는 필수입니다.")

        # -> 서비스가 코드/이름 둘 다 처리 (혹시 모르니)
        result = home_service.register_travel_country(
            uid=uid,
            country_code=req.country_code,
            country_name=req.country_name,
        )

        return {
            "success": True,
            "message": "여행 국가가 등록되었습니다.",
            "countryInfo": {"code": result["code"], "name": result["name"]},
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"여행 국가 등록 실패: {str(e)}")