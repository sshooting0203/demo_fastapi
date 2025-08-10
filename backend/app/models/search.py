from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .food import FoodInfo

# 간단한 검색 요청 모델 (언어 선택 + 국가)
class SimpleSearchRequest(BaseModel):
    query: str = Field(..., description="검색할 음식명 (OCR/번역 결과)")
    source_language: str = Field(..., description="원본 언어 코드 (예: ja)")
    target_language: str = Field(..., description="번역할 언어 코드 (예: ko)")
    country: Optional[str] = Field(None, description="국가 코드 (예: JP)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "초밥",
                "source_language": "ja",
                "target_language": "ko",
                "country": "JP"
            }
        }

# 간단한 검색 응답 모델 (카운트 포함)
class SimpleSearchResponse(BaseModel):
    foodId: str = Field(..., description="음식 ID")
    foodInfo: FoodInfo = Field(..., description="AI 분석된 음식 정보")
    isSaved: bool = Field(..., description="현재 사용자가 저장했는지 여부")
    searchCount: int = Field(..., description="현재 검색 횟수")