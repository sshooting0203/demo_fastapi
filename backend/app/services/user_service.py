from typing import Optional, List, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.user import User, SavedFood, SaveFoodRequest, DeleteSavedFoodsRequest
from app.models.food import FoodInfo
from app.db.firestore_client import firestore_client
from datetime import datetime
from firebase_admin import auth
import logging

logger = logging.getLogger(__name__)

# HTTP Bearer 인증을 위한 의존성
security = HTTPBearer()

class UserService:
    def __init__(self):
        self.db = firestore_client.db
    
    # ==================== 사용자 프로필 관리 ====================
    
    async def create_user(self, user_data: Dict[str, Any]) -> User:
        """새 사용자 생성 (OAuth 로그인 시 자동 생성)"""
        try:
            uid = user_data["uid"]
            current_time = datetime.now()
            
            # 기본 사용자 데이터 구성
            user_doc = {
                "uid": uid,
                "displayName": user_data.get("displayName", "새 사용자"),
                "email": user_data.get("email", ""),
                "allergies": user_data.get("allergies", []),
                "dietaryRestrictions": user_data.get("dietaryRestrictions", []),
                "currentCountry": user_data.get("currentCountry"),
                "createdAt": current_time,
                "updatedAt": current_time
            }
            
            # Firestore에 사용자 생성 (datetime은 Firestore가 자동으로 Timestamp로 변환)
            user_ref = self.db.collection('users').document(uid)
            user_ref.set(user_doc)
            
            logger.info(f"새 사용자 생성 완료: {uid}")
            return User(**user_doc)
            
        except Exception as e:
            logger.error(f"사용자 생성 실패: {str(e)}")
            raise Exception(f"사용자 생성 중 오류 발생: {str(e)}")
    
    async def create_or_update_user(self, user_data: Dict[str, Any]) -> User:
        """사용자 생성 또는 업데이트 (OAuth 로그인 시 사용)"""
        try:
            uid = user_data["uid"]
            
            # 기존 사용자 확인
            existing_user = await self.get_user_profile(uid)
            
            if existing_user:
                # 기존 사용자가 있으면 업데이트
                update_data = {
                    "displayName": user_data.get("displayName", existing_user.displayName),
                    "email": user_data.get("email", existing_user.email),
                    "updatedAt": datetime.now()
                }
                
                updated_user = await self.update_user_profile(uid, update_data)
                logger.info(f"기존 사용자 업데이트 완료: {uid}")
                return updated_user
            else:
                # 새 사용자 생성
                new_user = await self.create_user(user_data)
                logger.info(f"새 사용자 생성 완료: {uid}")
                return new_user
                
        except Exception as e:
            logger.error(f"사용자 생성/업데이트 실패: {str(e)}")
            raise Exception(f"사용자 생성/업데이트 중 오류 발생: {str(e)}")
    
    async def get_user_profile(self, uid: str) -> Optional[User]:
        """사용자 프로필 정보를 가져옵니다."""
        try:
            user_ref = self.db.collection('users').document(uid)
            doc = user_ref.get()
            
            if not doc.exists:
                logger.warning(f"사용자를 찾을 수 없음: {uid}")
                return None
            
            data = doc.to_dict()
            
            # datetime 필드 변환 (Firestore Timestamp 객체 처리)
            if 'createdAt' in data:
                if hasattr(data['createdAt'], 'timestamp'):
                    # Firestore Timestamp 객체인 경우
                    data['createdAt'] = datetime.fromtimestamp(data['createdAt'].timestamp())
                elif isinstance(data['createdAt'], str):
                    data['createdAt'] = datetime.fromisoformat(data['createdAt'])
            
            if 'updatedAt' in data:
                if hasattr(data['updatedAt'], 'timestamp'):
                    # Firestore Timestamp 객체인 경우
                    data['updatedAt'] = datetime.fromtimestamp(data['updatedAt'].timestamp())
                elif isinstance(data['updatedAt'], str):
                    data['updatedAt'] = datetime.fromisoformat(data['updatedAt'])
            
            return User(**data)
            
        except Exception as e:
            logger.error(f"사용자 프로필 조회 실패: {str(e)}")
            raise Exception(f"사용자 프로필 조회 중 오류 발생: {str(e)}")
    
    async def update_user_profile(self, uid: str, update_data: Dict[str, Any]) -> User:
        """사용자 프로필 정보를 업데이트합니다."""
        try:
            # updatedAt 필드 자동 업데이트 (Firestore가 자동으로 Timestamp로 변환)
            update_data["updatedAt"] = datetime.now()
            
            user_ref = self.db.collection('users').document(uid)
            user_ref.update(update_data)
            
            # 업데이트된 사용자 정보 반환
            updated_user = await self.get_user_profile(uid)
            if not updated_user:
                raise Exception("업데이트된 사용자 정보를 찾을 수 없습니다.")
            
            logger.info(f"사용자 프로필 업데이트 완료: {uid}")
            return updated_user
            
        except Exception as e:
            logger.error(f"사용자 프로필 업데이트 실패: {str(e)}")
            raise Exception(f"사용자 프로필 업데이트 중 오류 발생: {str(e)}")
    
    # MVP 단계에서는 사용하지 않음 - 나중에 필요시 주석 해제
    # async def update_allergies(self, uid: str, allergies: List[str]) -> User:
    #     """사용자의 알레르기 정보를 업데이트합니다."""
    #     try:
    #         update_data = {
    #             "allergies": allergies,
    #             "updatedAt": datetime.now()
    #         }
    #         
    #         return await self.update_user_profile(uid, update_data)
    #         
    #     except Exception as e:
    #         logger.error(f"알레르기 정보 업데이트 실패: {str(e)}")
    #         raise Exception(f"알레르기 정보 업데이트 중 오류 발생: {str(e)}")
    
    # MVP 단계에서는 사용하지 않음 - 나중에 필요시 주석 해제
    # async def update_dietary_restrictions(self, uid: str, restrictions: List[str]) -> User:
    #     """사용자의 식단 제한 정보를 업데이트합니다."""
    #     try:
    #         update_data = {
    #             "dietaryRestrictions": restrictions,
    #             "updatedAt": datetime.now()
    #         }
    #         
    #         return await self.update_user_profile(uid, update_data)
    #         
    #     except Exception as e:
    #         logger.error(f"식단 제한 정보 업데이트 실패: {str(e)}")
    #         raise Exception(f"식단 제한 정보 업데이트 중 오류 발생: {str(e)}")
    
    async def update_travel_country(self, uid: str, country_code: str) -> User:
        """사용자의 여행 국가를 업데이트합니다."""
        try:
            update_data = {
                "currentCountry": country_code,
                "updatedAt": datetime.now()
            }
            
            return await self.update_user_profile(uid, update_data)
            
        except Exception as e:
            logger.error(f"여행 국가 업데이트 실패: {str(e)}")
            raise Exception(f"여행 국가 업데이트 중 오류 발생: {str(e)}")
    
    # ==================== 저장된 음식 관리 ====================
    
    async def save_food(self, uid: str, save_request: SaveFoodRequest) -> SavedFood:
        """사용자가 음식을 저장합니다."""
        try:
            # 저장된 음식 데이터 구성
            saved_food = SavedFood(
                id=save_request.foodId,
                userImageUrl=save_request.userImageUrl,
                foodInfo=save_request.foodInfo,
                restaurantName=save_request.restaurantName,
                savedAt=datetime.now()
            )
            
            # Firestore에 저장 (users/{uid}/saved_foods 서브컬렉션)
            # datetime은 Firestore가 자동으로 Timestamp로 변환
            saved_food_ref = self.db.collection('users').document(uid).collection('saved_foods').document(save_request.foodId)
            saved_food_ref.set(saved_food.model_dump())
            
            logger.info(f"음식 저장 완료: 사용자 {uid}, 음식 {save_request.foodId}")
            return saved_food
            
        except Exception as e:
            logger.error(f"음식 저장 실패: {str(e)}")
            raise Exception(f"음식 저장 중 오류 발생: {str(e)}")
    
    async def get_user_saved_foods(self, uid: str) -> List[SavedFood]:
        """사용자가 저장한 음식 목록을 조회합니다. (마이페이지용)"""
        try:
            logger.info(f"저장된 음식 조회 시작: 사용자 {uid}")
            
            # 사용자의 저장된 음식 서브컬렉션에서 모든 문서 조회
            saved_foods_ref = self.db.collection('users').document(uid).collection('saved_foods')
            docs = saved_foods_ref.stream()
            
            saved_foods = []
            for doc in docs:
                data = doc.to_dict()
                
                # datetime 필드 변환 (Firestore Timestamp 객체 처리)
                if 'savedAt' in data:
                    if hasattr(data['savedAt'], 'timestamp'):
                        # Firestore Timestamp 객체인 경우
                        data['savedAt'] = datetime.fromtimestamp(data['savedAt'].timestamp())
                    elif isinstance(data['savedAt'], str):
                        data['savedAt'] = datetime.fromisoformat(data['savedAt'])
                
                # FoodInfo 모델 변환
                if 'foodInfo' in data:
                    try:
                        data['foodInfo'] = FoodInfo(**data['foodInfo'])
                    except Exception as e:
                        logger.warning(f"FoodInfo 모델 변환 실패: {str(e)}")
                        # 변환 실패 시 원본 데이터 유지
                        pass
                
                saved_foods.append(SavedFood(**data))
            
            logger.info(f"저장된 음식 조회 완료: 사용자 {uid}, {len(saved_foods)}개")
            return saved_foods
            
        except Exception as e:
            logger.error(f"저장된 음식 조회 실패: {str(e)}")
            raise Exception(f"저장된 음식 조회 중 오류 발생: {str(e)}")
    
    async def get_saved_food_by_id(self, uid: str, food_id: str) -> Optional[SavedFood]:
        """특정 저장된 음식을 조회합니다."""
        try:
            saved_food_ref = self.db.collection('users').document(uid).collection('saved_foods').document(food_id)
            doc = saved_food_ref.get()
            
            if not doc.exists:
                return None
            
            data = doc.to_dict()
            
            # datetime 필드 변환 (Firestore Timestamp 객체 처리)
            if 'savedAt' in data:
                if hasattr(data['savedAt'], 'timestamp'):
                    # Firestore Timestamp 객체인 경우
                    data['savedAt'] = datetime.fromtimestamp(data['savedAt'].timestamp())
                elif isinstance(data['savedAt'], str):
                    data['savedAt'] = datetime.fromisoformat(data['savedAt'])
            
            # FoodInfo 모델 변환
            if 'foodInfo' in data:
                try:
                    data['foodInfo'] = FoodInfo(**data['foodInfo'])
                except Exception as e:
                    logger.warning(f"FoodInfo 모델 변환 실패: {str(e)}")
                    # 변환 실패 시 원본 데이터 유지
                    pass
            
            return SavedFood(**data)
            
        except Exception as e:
            logger.error(f"저장된 음식 조회 실패: {str(e)}")
            raise Exception(f"저장된 음식 조회 중 오류 발생: {str(e)}")
    
    async def delete_saved_foods(self, uid: str, delete_request: DeleteSavedFoodsRequest) -> Dict[str, Any]:
        """사용자가 저장한 음식을 삭제합니다."""
        try:
            logger.info(f"음식 삭제 시작: 사용자 {uid}, 삭제할 음식 ID들: {delete_request.foodIds}")
            deleted_count = 0
            failed_deletions = []
            
            for food_id in delete_request.foodIds:
                try:
                    logger.info(f"음식 삭제 시도: {food_id}")
                    saved_food_ref = self.db.collection('users').document(uid).collection('saved_foods').document(food_id)
                    doc = saved_food_ref.get()
                    
                    if doc.exists:
                        logger.info(f"문서 존재 확인: {food_id}")
                        saved_food_ref.delete()
                        deleted_count += 1
                        logger.info(f"음식 삭제 완료: 사용자 {uid}, 음식 {food_id}")
                    else:
                        logger.warning(f"문서가 존재하지 않음: {food_id}")
                        failed_deletions.append(food_id)
                        
                except Exception as e:
                    logger.error(f"음식 삭제 실패: {food_id}, 오류: {str(e)}")
                    failed_deletions.append(food_id)
            
            result = {
                "success": True,
                "deletedCount": deleted_count,
                "failedDeletions": failed_deletions,
                "message": f"{deleted_count}개의 음식이 삭제되었습니다."
            }
            
            if failed_deletions:
                result["message"] += f" {len(failed_deletions)}개의 음식 삭제에 실패했습니다."
            
            logger.info(f"삭제 결과: {result}")
            return result
            
        except Exception as e:
            logger.error(f"음식 삭제 실패: {str(e)}")
            raise Exception(f"음식 삭제 중 오류 발생: {str(e)}")
    
    async def check_food_saved(self, uid: str, food_id: str) -> bool:
        """특정 음식이 사용자에게 저장되어 있는지 확인합니다."""
        try:
            saved_food_ref = self.db.collection('users').document(uid).collection('saved_foods').document(food_id)
            doc = saved_food_ref.get()
            
            return doc.exists
            
        except Exception as e:
            logger.error(f"음식 저장 여부 확인 실패: {str(e)}")
            return False
    
    async def get_saved_food_document_info(self, uid: str, food_id: str) -> Dict[str, Any]:
        """특정 저장된 음식 문서의 상세 정보를 조회합니다 (디버깅용)"""
        try:
            saved_food_ref = self.db.collection('users').document(uid).collection('saved_foods').document(food_id)
            doc = saved_food_ref.get()
            
            if not doc.exists:
                return {"exists": False, "message": "문서가 존재하지 않습니다."}
            
            data = doc.to_dict()
            return {
                "exists": True,
                "id": doc.id,
                "path": doc.reference.path,
                "data": data,
                "createTime": doc.create_time.isoformat() if hasattr(doc, 'create_time') else None,
                "updateTime": doc.update_time.isoformat() if hasattr(doc, 'update_time') else None
            }
            
        except Exception as e:
            logger.error(f"문서 정보 조회 실패: {str(e)}")
            return {"exists": False, "error": str(e)}
    
    # ==================== 사용자 통계 및 분석 ====================
    
    # MVP 단계에서는 사용하지 않음 - 나중에 필요시 주석 해제
    # async def get_user_stats(self, uid: str) -> Dict[str, Any]:
    #     """사용자의 통계 정보를 조회합니다."""
    #     try:
    #         # 저장된 음식 수
    #         saved_foods_ref = self.db.collection('users').document(uid).collection('saved_foods')
    #         saved_count = len(list(saved_foods_ref.stream()))
    #         
    #         # 사용자 프로필 정보
    #         user_profile = await self.get_user_profile(uid)
    #         
    #         stats = {
    #             "uid": uid,
    #             "savedFoodsCount": saved_count,
    #             "profile": user_profile.model_dump() if user_profile else None,
    #             "lastActivity": user_profile.updatedAt if user_profile else None
    #         }
    #         
    #         return stats
    #         
    #     except Exception as e:
    #         logger.error(f"사용자 통계 조회 실패: {str(e)}")
    #         raise Exception(f"사용자 통계 조회 중 오류 발생: {str(e)}")

# 서비스 인스턴스 생성
user_service = UserService()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[dict]:
    """Firebase 토큰을 검증하고 현재 사용자 정보를 반환합니다."""
    try:
        # Firebase 토큰 검증
        decoded_token = auth.verify_id_token(credentials.credentials)
        
        # 사용자 정보 반환
        user_info = {
            "uid": decoded_token["uid"],
            "email": decoded_token.get("email", ""),
            "displayName": decoded_token.get("name", ""),
            "emailVerified": decoded_token.get("email_verified", False)
        }
        
        logger.info(f"사용자 인증 성공: {user_info['uid']}")
        return user_info
        
    except Exception as e:
        logger.error(f"사용자 인증 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 토큰입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
