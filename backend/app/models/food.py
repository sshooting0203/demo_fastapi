from pydantic import BaseModel, Field
from typing import List, Optional

class FoodInfo(BaseModel):
    """음식 상세 정보 및 AI 응답 처리용"""
    foodName: str = Field(..., description="음식 이름(원어)", example="とんかつ")
    dishName: str = Field(..., description="음식 이름(한국어)", example="돈가스")
    country: str = Field(..., description="국가 코드 (예: JP, KR, US)", example="JP")
    summary: str = Field(..., description="음식 요약 설명", example="일본의 대표적인 돼지고기 튀김 요리입니다.")
    recommendations: List[str] = Field(default=[], description="추천 사용자 배열", example=["고기 좋아하는 사람", "튀김 요리 선호자"])
    ingredients: List[str] = Field(default=[], description="주요 재료", example=["돼지고기", "빵가루", "계란", "밀가루"])
    allergens: List[str] = Field(default=[], description="알레르기 성분 (allergy_codes와 일치)", example=["WHEAT", "EGG"])
    imageUrl: str = Field(..., description="음식 이미지 URL", example="https://example.com/tonkatsu.jpg")
    imageSource: Optional[str] = Field(None, description="이미지 출처", example="일본 요리 사진")
    culturalBackground: Optional[str] = Field(None, description="문화적 배경", example="일본 메이지 시대에 서양의 커틀릿을 참고하여 만들어진 요리입니다.")

class FoodSearchRequest(BaseModel):
    """음식 검색 요청"""
    query: str = Field(..., description="검색어")
    country_code: str = Field(default="JP", description="국가 코드")

class FoodCreateRequest(BaseModel):
    """음식 생성 요청"""
    name: str = Field(..., description="음식 이름")
    country_code: str = Field(default="JP", description="국가 코드")
    image_url: Optional[str] = Field(None, description="이미지 URL")


