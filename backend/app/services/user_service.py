from typing import Optional, List, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..models.user import User, SavedFood, SaveFoodRequest, DeleteSavedFoodsRequest
from ..models.food import FoodInfo
from ..db.firestore_client import firestore_client
from datetime import datetime
from firebase_admin import auth, firestore
import os
import logging

logger = logging.getLogger(__name__)

# HTTP Bearer 인증을 위한 의존성
security = HTTPBearer()

class UserService:
    """
    사용자 관리 서비스
    
    주요 기능:
    - 사용자 프로필 생성, 조회, 업데이트
    - 저장된 음식 관리 (저장, 조회, 삭제)
    - Firebase 인증 토큰 검증
    """
    
    def __init__(self):
        """UserService 초기화"""
        self.db = firestore_client.db
    
    # ==================== 사용자 프로필 관리 ====================
    
    async def create_user(self, user_data: Dict[str, Any]) -> User:
        """
        새 사용자 생성 (OAuth 로그인 시 자동 생성)
        
        Args:
            user_data (Dict[str, Any]): 사용자 데이터
                - uid: 사용자 ID
                - displayName: 표시명
                - email: 이메일
                - allergies: 알레르기 목록
                - dietaryRestrictions: 식단 제한
                - currentCountry: 현재 국가
                
        Returns:
            User: 생성된 사용자 객체
            
        Raises:
            Exception: 사용자 생성 실패 시
        """
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
            
            # Firestore에 사용자 생성
            user_ref = self.db.collection('users').document(uid)
            user_ref.set(user_doc)
            
            logger.info(f"새 사용자 생성 완료: {uid}")
            return User(**user_doc)
            
        except Exception as e:
            logger.error(f"사용자 생성 실패: {str(e)}")
            raise Exception(f"사용자 생성 중 오류 발생: {str(e)}")
    
    async def create_or_update_user(self, user_data: Dict[str, Any]) -> User:
        """
        사용자 생성 또는 업데이트 (OAuth 로그인 시 사용)
        
        Args:
            user_data (Dict[str, Any]): 사용자 데이터
            
        Returns:
            User: 생성되거나 업데이트된 사용자 객체
            
        Raises:
            Exception: 사용자 생성/업데이트 실패 시
        """
        try:
            uid = user_data["uid"]
            
            # 기존 사용자 확인
            user_ref = self.db.collection('users').document(uid)
            doc = user_ref.get()
            
            if doc.exists:
                # 기존 사용자가 있으면 업데이트
                update_data = {
                    "displayName": user_data.get("displayName", doc.to_dict().get("displayName", "")),
                    "email": user_data.get("email", doc.to_dict().get("email", "")),
                    "updatedAt": datetime.now()
                }
                
                user_ref.update(update_data)
                
                # 업데이트된 사용자 정보 반환
                updated_doc = user_ref.get()
                updated_data = updated_doc.to_dict()
                updated_data["uid"] = uid
                
                logger.info(f"기존 사용자 업데이트 완료: {uid}")
                return User(**updated_data)
            else:
                # 새 사용자 생성
                new_user = await self.create_user(user_data)
                logger.info(f"새 사용자 생성 완료: {uid}")
                return new_user
                
        except Exception as e:
            logger.error(f"사용자 생성/업데이트 실패: {str(e)}")
            raise Exception(f"사용자 생성/업데이트 중 오류 발생: {str(e)}")
    
    async def update_user(self, uid: str, update_data: Dict[str, Any]) -> User:
        """
        사용자 정보 통합 업데이트
        
        Args:
            uid (str): 사용자 ID
            update_data (Dict[str, Any]): 업데이트할 데이터
                - displayName: 표시명
                - email: 이메일
                - allergies: 알레르기 목록
                - dietaryRestrictions: 식단 제한
                - currentCountry: 현재 국가
                
        Returns:
            User: 업데이트된 사용자 객체
            
        Raises:
            Exception: 사용자 정보 업데이트 실패 시
        """
        try:
            # updatedAt 필드 자동 업데이트
            update_data["updatedAt"] = datetime.now()
            
            user_ref = self.db.collection('users').document(uid)
            user_ref.update(update_data)
            
            # 업데이트된 사용자 정보 반환
            updated_doc = user_ref.get()
            if not updated_doc.exists:
                raise Exception("업데이트된 사용자 정보를 찾을 수 없습니다.")
            
            updated_data = updated_doc.to_dict()
            updated_data["uid"] = uid
            
            logger.info(f"사용자 정보 업데이트 완료: {uid}")
            return User(**updated_data)
            
        except Exception as e:
            logger.error(f"사용자 정보 업데이트 실패: {str(e)}")
            raise Exception(f"사용자 정보 업데이트 중 오류 발생: {str(e)}")
    
    async def get_user_profile(self, uid: str) -> Optional[User]:
        """
        사용자 프로필 정보 조회
        
        Args:
            uid (str): 사용자 ID
            
        Returns:
            Optional[User]: 사용자 객체 또는 None (존재하지 않는 경우)
            
        Raises:
            Exception: 프로필 조회 실패 시
        """
        try:
            user_ref = self.db.collection('users').document(uid)
            doc = user_ref.get()
            
            if not doc.exists:
                logger.warning(f"사용자를 찾을 수 없음: {uid}")
                return None
            
            data = doc.to_dict()
            data["uid"] = uid
            
            # Firestore Timestamp 객체를 Python datetime으로 변환
            timestamp_fields = ['createdAt', 'updatedAt']
            for field in timestamp_fields:
                if field in data:
                    timestamp_value = data[field]
                    if hasattr(timestamp_value, 'timestamp'):
                        data[field] = datetime.fromtimestamp(timestamp_value.timestamp())
                    elif isinstance(timestamp_value, str):
                        try:
                            data[field] = datetime.fromisoformat(timestamp_value)
                        except ValueError:
                            pass
            
            return User(**data)
            
        except Exception as e:
            logger.error(f"사용자 프로필 조회 실패: {str(e)}")
            raise Exception(f"사용자 프로필 조회 중 오류 발생: {str(e)}")
    
    # ==================== 저장된 음식 관리 ====================
    
    async def save_food(self, uid: str, save_request: SaveFoodRequest) -> SavedFood:
        """
        사용자가 음식을 저장
        
        Args:
            uid (str): 사용자 ID
            save_request (SaveFoodRequest): 음식 저장 요청
            
        Returns:
            SavedFood: 저장된 음식 객체
            
        Raises:
            Exception: 음식 저장 실패 시
        """
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
            saved_food_ref = self.db.collection('users').document(uid).collection('saved_foods').document(save_request.foodId)
            saved_food_ref.set(saved_food.model_dump())
            
            # 메타데이터 업데이트 (저장 횟수 증가)
            await self._update_food_save_count(save_request.foodInfo)
            
            logger.info(f"음식 저장 완료: 사용자 {uid}, 음식 {save_request.foodId}")
            return saved_food
            
        except Exception as e:
            logger.error(f"음식 저장 실패: {str(e)}")
            raise Exception(f"음식 저장 중 오류 발생: {str(e)}")
    
    async def get_user_saved_foods(self, uid: str) -> List[SavedFood]:
        """
        사용자가 저장한 음식 목록 조회 (마이페이지용)
        
        Args:
            uid (str): 사용자 ID
            
        Returns:
            List[SavedFood]: 저장된 음식 목록
            
        Raises:
            Exception: 저장된 음식 조회 실패 시
        """
        try:
            logger.info(f"저장된 음식 조회 시작: 사용자 {uid}")
            
            # 사용자의 저장된 음식 서브컬렉션에서 모든 문서 조회
            saved_foods_ref = self.db.collection('users').document(uid).collection('saved_foods')
            docs = saved_foods_ref.stream()
            
            saved_foods = []
            for doc in docs:
                data = doc.to_dict()
                
                # Firestore Timestamp 객체를 Python datetime으로 변환
                timestamp_fields = ['savedAt']
                for field in timestamp_fields:
                    if field in data:
                        timestamp_value = data[field]
                        if hasattr(timestamp_value, 'timestamp'):
                            data[field] = datetime.fromtimestamp(timestamp_value.timestamp())
                        elif isinstance(timestamp_value, str):
                            try:
                                data[field] = datetime.fromisoformat(timestamp_value)
                            except ValueError:
                                pass
                
                # FoodInfo 모델 변환
                if 'foodInfo' in data:
                    try:
                        data['foodInfo'] = FoodInfo(**data['foodInfo'])
                    except Exception as e:
                        logger.warning(f"FoodInfo 모델 변환 실패: {str(e)}")
                        pass
                
                saved_foods.append(SavedFood(**data))
            
            logger.info(f"저장된 음식 조회 완료: 사용자 {uid}, {len(saved_foods)}개")
            return saved_foods
            
        except Exception as e:
            logger.error(f"저장된 음식 조회 실패: {str(e)}")
            raise Exception(f"저장된 음식 조회 중 오류 발생: {str(e)}")
    

    ############## 여기 로직은 좀 더 고민민
    async def _update_food_save_count(self, food_info: FoodInfo):
        """음식 저장 시 메타데이터의 저장 횟수 업데이트 (없으면 생성)"""
        try:
            # 문서명 생성: 나라코드_음식영문명
            doc_name = f"{food_info.country}_{food_info.foodName}"
            
            # 메타데이터 참조
            meta_ref = self.db.collection('food_metadata').document(doc_name)
            
            # 현재 문서 확인
            doc = meta_ref.get()
            
            if doc.exists:
                # 기존 문서: 저장 횟수 증가
                current_count = doc.to_dict().get('saveCount', 0)
                meta_ref.update({
                    'saveCount': current_count + 1,
                    'lastSavedAt': datetime.now()
                })
            else:
                # 새 문서 생성
                meta_ref.set({
                    'country': food_info.country,
                    'foodName': food_info.foodName,
                    'saveCount': 1,
                    'searchCount': 1,  # 검색 횟수도 초기화
                    'createdAt': datetime.now(),
                    'lastSavedAt': datetime.now()
                })
                
            logger.info(f"메타데이터 저장 횟수 증가: {doc_name}")
            
        except Exception as e:
            logger.error(f"메타데이터 업데이트 실패: {str(e)}")
            # 에러가 있어도 음식 저장은 계속 진행
    
    async def increase_search_count(self, food_info: FoodInfo):
        """음식 검색 시 메타데이터 검색 횟수 증가 (없으면 생성)"""
        try:
            # 문서명 생성: 나라코드_음식영문명
            doc_name = f"{food_info.country}_{food_info.foodName}"
            
            # 메타데이터 참조
            meta_ref = self.db.collection('food_metadata').document(doc_name)
            
            # 현재 문서 확인
            doc = meta_ref.get()
            
            if doc.exists:
                # 기존 문서: 검색 횟수 증가
                current_count = doc.to_dict().get('searchCount', 0)
                meta_ref.update({
                    'searchCount': current_count + 1,
                    'lastSearchedAt': datetime.now()
                })
            else:
                # 새 문서 생성
                meta_ref.set({
                    'country': food_info.country,
                    'foodName': food_info.foodName,
                    'searchCount': 1,
                    'saveCount': 0,  # 저장 횟수도 초기화
                    'createdAt': datetime.now(),
                    'lastSearchedAt': datetime.now()
                })
                
            logger.info(f"메타데이터 검색 횟수 증가: {doc_name}")
            
        except Exception as e:
            logger.error(f"메타데이터 업데이트 실패: {str(e)}")
            # 에러가 있어도 AI 분석은 계속 진행
    
    async def delete_saved_foods(self, uid: str, delete_request: DeleteSavedFoodsRequest) -> Dict[str, Any]:
        """
        사용자가 저장한 음식 일괄 삭제
        
        Args:
            uid (str): 사용자 ID
            delete_request (DeleteSavedFoodsRequest): 삭제 요청 (foodIds 배열)
            
        Returns:
            Dict[str, Any]: 삭제 결과
                - success: 성공 여부
                - deletedCount: 삭제된 음식 수
                - failedDeletions: 삭제 실패한 음식 ID 목록
                - message: 결과 메시지
                
        Raises:
            Exception: 음식 삭제 실패 시
        """
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
                        
                        # 삭제 전에 음식 정보를 가져와서 메타데이터 업데이트
                        food_data = doc.to_dict()
                        if 'foodInfo' in food_data:
                            try:
                                food_info = FoodInfo(**food_data['foodInfo'])
                                await self._decrease_food_save_count(food_info)
                            except Exception as e:
                                logger.warning(f"메타데이터 업데이트 실패: {str(e)}")
                        
                        saved_food_ref.delete()
                        deleted_count += 1
                        logger.info(f"음식 삭제 완료: 사용자 {uid}, 음식 {food_id}")
                    else:
                        logger.warning(f"문서가 존재하지 않음: {food_id}")
                        failed_deletions.append(food_id)
                        
                except Exception as e:
                    logger.error(f"음식 삭제 실패: {food_id}, 오류: {str(e)}")
                    failed_deletions.append(food_id)
            
            # 결과 구성
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

# 서비스 인스턴스 생성
user_service = UserService()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[dict]:
    """
    Firebase 토큰을 검증하고 현재 사용자 정보를 반환
    
    Args:
        credentials (HTTPAuthorizationCredentials): HTTP Bearer 토큰
        
    Returns:
        Optional[dict]: 사용자 정보 또는 None
        
    Raises:
        HTTPException: 토큰 검증 실패 시
    """
    token = credentials.credentials
    is_emulator = bool(os.getenv("FIREBASE_AUTH_EMULATOR_HOST"))

    try:
        # 에뮬레이터 토큰은 check_revoked/issuer 검사를 끄는 게 안전
        decoded = auth.verify_id_token(token, check_revoked=not is_emulator)

        user_info = {
            "uid": decoded["uid"],
            "email": decoded.get("email", ""),
            "displayName": decoded.get("name", ""),
            "emailVerified": decoded.get("email_verified", False),
        }
        logger.info(f"사용자 인증 성공: {user_info['uid']}")
        return user_info

    except Exception as e:
        logger.error(f"[auth] verify_id_token 실패 (emulator={is_emulator}): {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 토큰입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
