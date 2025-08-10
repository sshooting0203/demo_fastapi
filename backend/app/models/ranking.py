from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from .food import FoodInfo

# 홈화면에서 나라별 음식 텍스트 상위 3개 띄우기만 하면 됨

class TopFoodSnapshot(BaseModel):
    # 상위 음식 스냅샷 (홈 화면 빠른 응답용) -> 아래 코드에서 계산된 상위 3개 바로 표시 가능하게 
    foodId: str = Field(..., description="음식 ID (예: JP_tonkatsu)")
    country: str = Field(..., description="국가 코드 (예: JP)") # 국가 구분용
    foodName: str = Field(..., description="음식 이름")
    dishName: str = Field(default="", description="영어/일본어 음식 이름")
    searchCount: int = Field(..., description="검색 횟수") # 이건 로그찍기 개념으로 넣은 필드(테스트용)
    saveCount: int = Field(..., description="저장 횟수")

class CountryRanking(BaseModel):
    # 국가별 음식 랭킹 정보
    # 기존 CountryRankingFood를 배열 형태로 변경
    # 
    # 동작 방식:
    # 1. 검색/저장 시 해당 음식의 카운트 증가
    # 2. 카운트가 변경되면 topFoods 배열을 재정렬
    # 3. 홈화면에서는 topFoods[:3]만 가져와서 표시
    country: str = Field(..., description="국가 코드 (예: JP)")
    topFoods: List[TopFoodSnapshot] = Field(default=[], description="상위 배열 음식 (검색/저장 횟수 기준)")
    updatedAt: datetime = Field(..., description="마지막 업데이트 시간 (랭킹이 변경된 시점)")
