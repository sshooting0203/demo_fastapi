from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime

class FoodNames(BaseModel):
    # 다국어 음식 이름, 필요할까 싶어서 만들긴 함. 안 쓸 수도?
    default: str = Field(..., description="기본 이름")
    ko: str = Field(..., description="한국어 이름")
    en: Optional[str] = Field(None, description="영어 이름")

class FoodInfo(BaseModel):
    # 음식 상세 정보 및 ai에게서 받은 내용 처리할 클래스
    summary: str = Field(..., description="음식 요약 설명")
    recommendations: List[str] = Field(default=[], description="추천 사용자 배열")
    ingredients: List[str] = Field(default=[], description="주요 재료")
    allergens: List[str] = Field(default=[], description="알레르기 성분")
    imageUrl: str = Field(..., description="음식 이미지 URL (첫 업로드 이미지 X, 별도 선정)")
    imageSource: Optional[str] = Field(None, description="이미지 출처 (크롤링 시 사용)")
    culturalBackground: Optional[str] = Field(None, description="문화적 배경")
