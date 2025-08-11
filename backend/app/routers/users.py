from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from ..models.user import User, UserUpdate, SavedFood, SaveFoodRequest, DeleteSavedFoodsRequest
from ..services.user_service import user_service, get_current_user

router = APIRouter(prefix="/api/users", tags=["사용자"])


@router.get("/me", response_model=User)
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """내 프로필 조회"""
    try:
        uid = current_user["uid"]
        user = await user_service.get_user_profile(uid)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/me", response_model=User)
async def update_my_profile(
    profile_update: UserUpdate,
    current_user: dict = Depends(get_current_user),
):
    """
    프로필 수정 (이름, 알러지/식이, currentCountry 포함)
    - 비어 있는 필드는 무시(부분 업데이트)
    """
    try:
        uid = current_user["uid"]
        updated_user = await user_service.update_user(uid, profile_update.model_dump(exclude_unset=True))
        if not updated_user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        return updated_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/me/saved-foods", response_model=List[SavedFood])
async def get_my_saved_foods(current_user: dict = Depends(get_current_user)):
    """내 저장 목록"""
    try:
        uid = current_user["uid"]
        saved_foods = await user_service.get_user_saved_foods(uid)
        return saved_foods
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"저장된 음식 조회 중 오류: {str(e)}")


'''
# ai 부분에서 추가하도록
@router.post("/me/saved-foods", response_model=SavedFood)
async def save_food_to_my_list(
    save_request: SaveFoodRequest,
    current_user: dict = Depends(get_current_user),
):
    """음식 저장"""
    try:
        uid = current_user["uid"]
        saved_food = await user_service.save_food(uid, save_request)
        return saved_food
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"음식 저장 중 오류: {str(e)}")
'''

@router.delete("/me/saved-foods")
async def delete_my_saved_foods(
    delete_request: DeleteSavedFoodsRequest,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """저장된 음식 일괄 삭제 (foodIds 배열)"""
    try:
        uid = current_user["uid"]
        result = await user_service.delete_saved_foods(uid, delete_request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"음식 삭제 중 오류: {str(e)}")
