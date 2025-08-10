# @ Test Complete
from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.search import SimpleSearchRequest, SimpleSearchResponse
from app.services.search_service import SearchService
from app.services.ranking_service import RankingService
from app.services.user_service import get_current_user
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/search", tags=["검색"])
search_service = SearchService()
ranking_service = RankingService()

@router.post("/", response_model=SimpleSearchResponse)
async def search_food(
    request: SimpleSearchRequest,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """음식 검색 API - MVP: OCR/번역 결과를 AI 음식 설명으로 변환"""
    try:
        uid = current_user.get('uid') if current_user else None
        
        # 1. 음식 검색 실행 (AI 음식 설명 생성)
        result = await search_service.search_food(request, uid)
        logging.info('res : %s', result)
        
        # 2. 검색 로그 저장 (간단하게)
        if uid:
            await search_service.log_search(uid, request.food_name, request.country)
        
        # 3. 국가별 랭킹 업데이트 (간단하게)
        if request.country:
            await ranking_service.update_country_ranking(request.country, request.food_name)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rankings/{country_code}")
async def get_country_rankings(
    country_code: str,
    limit: int = Query(3, description="조회할 랭킹 수 (기본값: 3)")
):
    """특정 국가의 음식 랭킹 조회 (MVP: 홈 화면 Top 3용)"""
    try:
        top_foods = await ranking_service.get_top_foods(country_code, limit)
        return {
            "success": True,
            "country": country_code,
            "rankings": top_foods,
            "count": len(top_foods)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"랭킹 조회 실패: {str(e)}")