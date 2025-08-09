from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

# SearchRequest 모델 country, originalText, translatedText, foodId
class SearchRequest(BaseModel):
    country: str = Field(..., description="국가 코드 (예: JP)") # country 2글자
    originalText: str = Field(..., description="원본 검색어 (예: とんかつ)")
    translatedText: str = Field(..., description="번역된 검색어 (예: 돈카츠)")
    foodId: Optional[str] = Field(None, description="음식 ID (예: JP_tonkatsu) 없으면 서버가 생성")
    
    class Config: # swagger 문서 생성 시 예시 값 표시용
        schema_extra = {
            "example": {
                "countryCode": "JP",
                "originalText": "とんかつ",
                "translatedText": "돈카츠",
                "foodId": "JP_tonkatsu"
            }
        }

# search_logs 컬렉션의 메타데이터 역할이라고 봐야 함 
# -> 아직 삭제되기 전에 ai가 번역/분석한 게 남았네(ai 또 호출 방지)
class SearchLog(BaseModel):
    # 검색 로그 모델 (TTL 처리 필요) 
    # 모든 검색을 일단 searchLog에 저장한다고 생각각
    logId: str = Field(..., description="로그 ID")
    uid: Optional[str] = Field(None, description="사용자 ID")
    country: str = Field(..., description="국가 코드 (예: JP)")
    foodId: str = Field(..., description="음식 ID (예: JP_tonkatsu)")
    originalText: str = Field(..., description="원본 검색어")
    translatedText: str = Field(..., description="번역된 검색어")
    searchType: str = Field(..., description="검색 타입")
    timestamp: datetime = Field(..., description="검색 시간") # 이건 기록 제대로 하는지 보게 찍는 게 나을 것 같아서
    retentionDays: int = Field(..., description="보관 기간 (일)")