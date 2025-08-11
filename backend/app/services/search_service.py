from firebase_admin import firestore
from firebase_admin.firestore import Increment
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from ..models.search import SimpleSearchRequest, SimpleSearchResponse
from ..models.food import FoodInfo
from ..db.firestore_client import firestore_client
import logging

logger = logging.getLogger(__name__)

class SearchService:
    """
    음식 해석 서비스
    
    주요 기능:
    - OCR/번역 결과를 AI 음식 설명으로 변환
    - 검색 로그 저장 및 관리 (TTL 자동 처리)
    - 중복 검색 최적화
    - 음식 검색 통계 제공
    """
    
    def __init__(self):
        self.db = firestore_client.db
    
    async def search_food(self, request: SimpleSearchRequest, uid: Optional[str] = None) -> SimpleSearchResponse:
        """
        음식 검색 및 AI 해석
        
        Args:
            request (SimpleSearchRequest): 검색 요청 (OCR/번역 결과)
            uid (Optional[str]): 사용자 ID (로그인한 경우)
            
        Returns:
            SimpleSearchResponse: AI가 해석한 음식 정보
        """
        try:
            # 1단계: 메타데이터에서 동일한 음식 검색 (AI 비용 절약)
            existing_metadata = await self._find_existing_food_metadata(request.query, request.country)
            
            if existing_metadata:
                logger.info(f"기존 음식 메타데이터 발견: {existing_metadata['foodName']}")
                
                # 기존 음식 정보로 응답 생성
                food_info = await self._get_food_info_from_metadata(existing_metadata)
                
                # 검색 결과 저장 (중복이지만 사용자별 기록용)
                if uid:
                    await self._save_search_result(uid, request.query, existing_metadata['foodId'], food_info)
                    await self._update_food_search_count(request.query, request.country)
                
                # 검색 횟수 조회
                search_count = existing_metadata['searchCount']
                
                return SimpleSearchResponse(
                    foodId=existing_metadata['foodId'],
                    foodInfo=food_info,
                    isSaved=False,
                    searchCount=search_count
                )
            
            # 2단계: 새로운 음식인 경우 AI 해석 실행
            logger.info(f"새로운 음식 AI 해석 시작: {request.query}")
            
            # 임시 구현 (AI 로직은 나중에 연결)
            food_id = f"{request.country}_{request.query[:5]}"  # 국가_음식명 형태로 ID 생성
            
            # AI 음식 설명 생성 (임시 데이터)
            food_info = FoodInfo(
                foodName=request.query,
                dishName=request.query,
                country=request.country or "JP",
                summary="이 음식에 대한 AI 설명이 여기에 표시됩니다.",
                recommendations=["음식을 좋아하는 사람"],
                ingredients=["재료1", "재료2"],
                allergens=["알러지 정보"],
                imageUrl="https://example.com/placeholder.jpg",
                imageSource="AI 생성",
                culturalBackground="문화/역사 정보"
            )
            
            # 검색 결과를 Firestore에 저장 (TTL 자동 처리)
            if uid:
                await self._save_search_result(uid, request.query, food_id, food_info)
            
            # 검색 횟수 조회
            search_count = await self._get_search_count(food_id)
            
            # 응답 생성
            response = SimpleSearchResponse(
                foodId=food_id,
                foodInfo=food_info,
                isSaved=False,
                searchCount=search_count
            )
            
            # 검색 시 해당 음식의 카운트 업데이트
            if uid:
                await self._update_food_search_count(request.query, request.country or "JP")
            
            return response
            
        except Exception as e:
            logger.error(f"음식 검색 실패: {str(e)}")
            raise Exception(f"음식 검색 중 오류 발생: {str(e)}")
    
    async def _get_existing_search_result(self, uid: str, query: str) -> Optional[SimpleSearchResponse]:
        """
        기존 검색 결과 조회 (중복 검색 최적화)
        
        Args:
            uid (str): 사용자 ID
            query (str): 검색 쿼리
            
        Returns:
            Optional[SimpleSearchResponse]: 기존 검색 결과 또는 None
        """
        try:
            # 최근 24시간 내 같은 사용자의 같은 검색 결과 조회
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            search_results = self.db.collection('search_results').where('uid', '==', uid)\
                .where('query', '==', query)\
                .where('timestamp', '>', cutoff_time)\
                .order_by('timestamp', direction=firestore.Query.DESCENDING)\
                .limit(1)\
                .stream()
            
            for doc in search_results:
                data = doc.to_dict()
                if data:
                    # FoodInfo 모델 재구성
                    food_info = FoodInfo(**data.get('foodInfo', {}))
                    
                    return SimpleSearchResponse(
                        foodId=data.get('foodId'),
                        foodInfo=food_info,
                        isSaved=data.get('isSaved', False),
                        searchCount=data.get('searchCount', 0)
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"기존 검색 결과 조회 실패: {str(e)}")
            return None
    
    async def _save_search_result(self, uid: str, query: str, food_id: str, food_info: FoodInfo):
        """
        검색 결과를 Firestore에 저장 (중복 방지, TTL 자동 처리)
        
        Args:
            uid (str): 사용자 ID
            query (str): 검색 쿼리
            food_id (str): 음식 ID
            food_info (FoodInfo): 음식 정보
        """
        try:
            # 사용자별로 음식 ID 기준으로 중복 방지
            # 문서 ID를 "{uid}_{food_id}" 형태로 생성하여 중복 방지
            doc_id = f"{uid}_{food_id}"
            
            result_data = {
                'uid': uid,
                'query': query,
                'foodId': food_id,
                'foodInfo': food_info.model_dump(),
                'timestamp': datetime.now(),
                'updatedAt': datetime.now()
                # TTL 필드 제거 - Firestore에서 자동 처리
            }
            
            # Firestore에 검색 결과 저장 (중복 시 덮어쓰기)
            doc_ref = self.db.collection('search_results').document(doc_id)
            doc_ref.set(result_data)
            
            logger.info(f"검색 결과 저장 완료: {doc_id} (중복 방지)")
            
        except Exception as e:
            logger.error(f"검색 결과 저장 실패: {str(e)}")
    
    async def _get_search_count(self, food_id: str) -> int:
        """
        특정 음식의 검색 횟수 조회 (food_metadata 기반)
        
        Args:
            food_id (str): 음식 ID
            
        Returns:
            int: 검색 횟수
        """
        try:
            # food_metadata에서 해당 음식의 searchCount 직접 조회
            doc = self.db.collection('food_metadata').document(food_id).get()
            if doc.exists:
                data = doc.to_dict()
                return data.get('searchCount', 0)
            return 0
            
        except Exception as e:
            logger.error(f"검색 횟수 조회 오류: {str(e)}")
            return 0
    
    async def _update_food_search_count(self, food_name: str, country: str):
        """
        검색 시 해당 음식의 카운트를 업데이트 (food_metadata 기반)
        메타데이터가 없으면 새로 생성
        
        Args:
            food_name (str): 음식 이름
            country (str): 국가 코드
        """
        try:
            # food_metadata에서 해당 국가의 음식을 찾아서 searchCount 업데이트
            query = self.db.collection('food_metadata')\
                .where('country', '==', country)\
                .where('foodName', '==', food_name)
            
            docs = query.stream()
            for doc in docs:
                # 검색 횟수 증가 및 마지막 검색 시간 업데이트
                doc.reference.update({
                    'searchCount': Increment(1),
                    'lastSearched': datetime.now().isoformat(),
                    'updatedAt': datetime.now().isoformat()
                })
                logger.info(f"음식 카운트 업데이트 완료: {country} - {food_name}")
                return
            
            # 메타데이터가 없는 경우 새로 생성
            logger.info(f"새로운 음식 메타데이터 생성: {country} - {food_name}")
            
            # 문서 ID 생성 (country_dishName 형태)
            dish_name = food_name.lower().replace(' ', '_')  # 간단한 변환
            doc_id = f"{country}_{dish_name}"
            
            # 메타데이터 생성
            metadata = {
                'country': country,
                'foodName': food_name,
                'dishName': dish_name,
                'searchCount': 1,  # 최초 검색이므로 1
                'saveCount': 0,    # 저장 횟수
                'lastSearched': datetime.now().isoformat(),
                'updatedAt': datetime.now().isoformat()
            }
            
            # Firestore에 저장
            self.db.collection('food_metadata').document(doc_id).set(metadata)
            logger.info(f"새로운 음식 메타데이터 생성 완료: {doc_id}")
            
        except Exception as e:
            logger.error(f"음식 카운트 업데이트 실패: {str(e)}")

    async def cleanup_old_search_logs(self, days: int = 30):
        """
        오래된 검색 로그 정리 (백업용) - 삭제됨
        """
        # search_logs 컬렉션이 삭제되어 이 메서드는 더 이상 사용되지 않음
        pass

    async def get_top_foods_by_country(self, country: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        국가별 상위 음식 조회 (food_metadata 기반)
        
        Args:
            country (str): 국가 코드 (예: "JP", "KR")
            limit (int): 조회할 음식 수 (기본값: 3)
            
        Returns:
            List[Dict[str, Any]]: 상위 음식 목록 (foodId, foodName, dishName, searchCount, saveCount 포함)
        """
        try:
            # food_metadata에서 해당 국가의 음식들을 searchCount 기준으로 정렬하여 상위 limit개 조회
            query = self.db.collection('food_metadata')\
                .where('country', '==', country)\
                .order_by('searchCount', direction=firestore.Query.DESCENDING)\
                .limit(limit)
            logging.info('query :  %s', query)

            docs = query.stream()
            top_foods = []
            
            for doc in docs:
                data = doc.to_dict()
                food_data = {
                    'foodId': doc.id,  # 문서 ID (예: JP_tonkatsu)
                    'foodName': data.get('foodName', ''),  # 한국어 이름
                    'dishName': data.get('dishName', ''),  # 영어/일본어 이름
                    'searchCount': data.get('searchCount', 0),
                    'saveCount': data.get('saveCount', 0),
                    'lastSearched': data.get('lastSearched'),
                    'country': data.get('country', '')
                }
                top_foods.append(food_data)
            
            logger.info(f"국가 {country}의 상위 {len(top_foods)}개 음식 조회 완료")
            return top_foods
            
        except Exception as e:
            logger.error(f"상위 음식 조회 오류: {str(e)}")
            return []

# 싱글톤 인스턴스
search_service = SearchService()
