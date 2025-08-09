from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

# 홈화면에서 나라별 음식 텍스트 상위 3개 띄우기만 하면 됨

class TopFoodSnapshot(BaseModel):
    # 상위 음식 스냅샷 (홈 화면 빠른 응답용) -> 아래 코드에서 계산된 상위 3개 바로 표시 가능하게 
    foodId: str = Field(..., description="음식 ID (예: JP_tonkatsu)")
    country: str = Field(..., description="국가 코드 (예: JP)") # 국가 구분용
    foodName: str = Field(..., description="음식 이름")
    searchCount: int = Field(..., description="검색 횟수") # 이건 로그찍기 개념으로 넣은 필드(테스트용)
    saveCount: int = Field(..., description="저장 횟수")

class CountryRankingFood(BaseModel):
    # 국가별 음식 랭킹 정보 (카운트 원장) -> 전체 음식 검색/저장횟수 추적용
    foodId: str = Field(..., description="음식 ID")
    searchCount: int = Field(..., description="검색 횟수")
    saveCount: int = Field(..., description="저장 횟수")
    lastSearchedAt: datetime = Field(..., description="마지막 검색 시간")
    lastSavedAt: datetime = Field(..., description="마지막 저장 시간")
