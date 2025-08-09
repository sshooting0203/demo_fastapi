from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from .food import FoodInfo

class User(BaseModel):
    # 사용자 정보 모델
    uid: str = Field(..., description="사용자 고유 ID")
    email: Optional[str] = Field(None, description="이메일 (OAuth 구현에 따라 변경 가능)")
    allergies: List[str] = Field(default=[], description="알레르기 코드 목록 (allergy_codes 반영)")
    dietaryRestrictions: List[str] = Field(default=[], description="식단 제한 코드 목록 (dietary_codes 반영)")
    currentCountry: Optional[str] = Field(None, description="최근 여행국 (수정까지 유지, 기본 NULL 허용)")
    createdAt: datetime = Field(..., description="생성 시각")
    updatedAt: datetime = Field(..., description="수정 시각")

class SavedFood(BaseModel):
    # 유저 별 저장된 음식 모델 (users 내 서브컬렉션) -> 여기선 ai에게 받은 그대로 저장해야 하는 게 맞음
    id: str = Field(..., description="음식 ID")
    country: str = Field(..., description="국가 코드 (예: JP)")
    foodName: str = Field(..., description="음식 이름(기존)")
    translatedText: str = Field(..., description="번역된 텍스트(한글)")
    userImageUrl: str = Field(..., description="사용자가 업로드한 이미지 URL")
    foodInfo: FoodInfo = Field(..., description="음식 상세 정보") # ai로 응답 받은 그대로 저장해야 나중에 그대로 뜨니 수정
    restaurantName: str = Field(..., description="식당 이름(기존) (부가 기능?)")
    savedAt: datetime = Field(..., description="저장 시간")
    review: Optional[str] = Field(None, description="리뷰 (부가 기능)")
    rating: Optional[float] = Field(None, description="평점 (부가 기능)")