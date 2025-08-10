from fastapi import APIRouter, Depends, HTTPException
from ..models.search import SimpleSearchRequest, SimpleSearchResponse
from ..services.search_service import SearchService
from ..services.user_service import get_current_user
from typing import Optional

router = APIRouter(prefix="/api/foods", tags=["음식"])
search_service = SearchService()

@router.post("/interpret", response_model=SimpleSearchResponse)
async def interpret_food(
    request: SimpleSearchRequest,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """OCR/번역 결과 → 음식 설명 (AI 해석)"""
    try:
        uid = current_user.get('uid') if current_user else None
        
        # 음식 해석 실행 (검색 로그 저장 포함)
        result = await search_service.search_food(request, uid)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))