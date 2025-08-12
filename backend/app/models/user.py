from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from .food import FoodInfo

class User(BaseModel):
    # 사용자 정보 모델 (읽기용)
    uid: str = Field(..., description="사용자 고유 ID")
    displayName: str = Field(..., description="사용자 표시 이름 (OAuth에서 가져온 이름)")
    email: Optional[str] = Field(None, description="이메일 (OAuth 구현에 따라 변경 가능)")
    allergies: List[str] = Field(default_factory=list, description="알레르기 코드 목록 (allergy_codes 반영)")
    dietaryRestrictions: List[str] = Field(default_factory=list, description="식단 제한 코드 목록 (dietary_codes 반영)")
    currentCountry: Optional[str] = Field(None, description="최근 여행국 (수정까지 유지, 기본 NULL 허용)")
    createdAt: datetime = Field(..., description="생성 시각")
    updatedAt: datetime = Field(..., description="수정 시각")


# 한 방 업데이트용 DTO (PUT /api/users/me)
class UserUpdate(BaseModel):
    """
    사용자 프로필 업데이트 요청 모델
    - 모두 선택 입력
    - 비어 있는 필드는 병합 시 무시됨(서버에서 whitelist + merge=True)
    """
    displayName: Optional[str] = Field(None, description="사용자 표시 이름")
    email: Optional[EmailStr] = Field(None, description="이메일(선택)")
    allergies: Optional[List[str]] = Field(None, description="알레르기 코드 목록")
    dietaryRestrictions: Optional[List[str]] = Field(None, description="식단 제한 코드 목록")
    currentCountry: Optional[str] = Field(None, description="여행 중인 나라(국가코드)")


class SavedFood(BaseModel):
    # 유저 별 저장된 음식 모델 (users/{uid}/saved_foods/*)
    id: str = Field(..., description="음식 ID (예: JP_tonkatsu, KR_bibimbap) - 중복 저장 방지용", example="JP_tonkatsu")
    userImageUrl: Optional[str] = Field(None, description="사용자가 업로드한 이미지 URL", example="https://example.com/user_uploaded_image.jpg")
    foodInfo: FoodInfo = Field(..., description="AI 분석 결과 음식 상세 정보 - 수정하지 말고 그대로 저장해야 함")
    restaurantName: Optional[str] = Field(None, description="식당 이름 (선택사항)", example="도쿄 돈가스점")
    savedAt: datetime = Field(..., description="음식 저장 시간 (서버에서 자동 설정)", example="2024-01-15T10:30:00")
    personalized_info: Optional[Dict[str, Any]] = Field(None, description="개인화 정보 (알레르기, 식단제한 등)")


class SaveFoodRequest(BaseModel):
    """음식 저장 요청 모델 - AI 응답과 호환"""
    # AI 응답의 data 부분을 그대로 받음
    data: Dict[str, Any] = Field(..., description="AI 응답의 data 부분")
    
    # 추가 정보 (사용자가 입력)
    userImageUrl: Optional[str] = Field(None, description="사용자 업로드 이미지")
    restaurantName: Optional[str] = Field(None, description="식당 이름")
    
    # 개인화 정보 (AI 응답에서)
    personalized_info: Optional[Dict[str, Any]] = Field(None, description="개인화 정보")


class DeleteSavedFoodsRequest(BaseModel):
    """저장된 음식 삭제 요청 모델"""
    foodIds: List[str] = Field(..., description="삭제할 음식 ID 목록", example=["JP_tonkatsu", "KR_bibimbap"])
