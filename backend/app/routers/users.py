from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from ..models.user import User, UserProfileUpdate, SavedFood, SaveFoodRequest, DeleteSavedFoodsRequest
from ..services.user_service import user_service, get_current_user
from ..services.home_service import home_service

router = APIRouter(prefix="/api/users", tags=["사용자"])

@router.get("/{uid}/profile", response_model=User)
async def get_user_profile(uid: str):
    """사용자 프로필 조회 (MVP: 마이페이지용)"""
    try:
        user = await user_service.get_user_profile(uid)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{uid}/profile", response_model=User)
async def update_user_profile(uid: str, profile_update: UserProfileUpdate):
    """사용자 프로필 업데이트 (MVP: 이름, 여행국가 변경)"""
    try:
        updated_user = await user_service.update_user_profile(uid, profile_update.model_dump())
        if not updated_user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        return updated_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{uid}/saved-foods", response_model=List[SavedFood])
async def get_saved_foods(uid: str):
    """사용자가 저장한 음식 목록 조회 (MVP: 마이페이지용)"""
    try:
        saved_foods = await user_service.get_user_saved_foods(uid)
        return saved_foods
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"저장된 음식 조회 중 오류 발생: {str(e)}")

@router.post("/{uid}/save-food", response_model=SavedFood)
async def save_food(uid: str, save_request: SaveFoodRequest):
    """음식 저장 (MVP: AI 음식 설명을 유저의 하위 컬렉션에 저장)"""
    try:
        saved_food = await user_service.save_food(uid, save_request)
        return saved_food
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"음식 저장 중 오류 발생: {str(e)}")

@router.delete("/{uid}/delete-foods")
async def delete_saved_foods(uid: str, delete_request: DeleteSavedFoodsRequest):
    """저장된 음식 삭제 (MVP: 여러 개 선택 후 일괄 삭제)"""
    try:
        result = await user_service.delete_saved_foods(uid, delete_request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"음식 삭제 중 오류 발생: {str(e)}")
