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
    
    async def _save_search_result(self, uid: str, query: str, food_id: str, food_info: FoodInfo):
        """
        검색 결과를 Firestore에 저장 (AI 분석 결과 포함)
        
        Args:
            uid (str): 사용자 ID
            query (str): 검색 쿼리 (원어 음식명)
            food_id (str): 음식 ID ({나라코드두글자}_{foodName} 형태)
            food_info (FoodInfo): AI 분석된 음식 정보
        """
        try:
            # 문서 ID를 food_id와 동일하게 설정 ({나라코드두글자}_{foodName})
            doc_id = food_id
            
            result_data = {
                'uid': uid,
                'query': query.lower(),  # 검색 요청한 원어 음식명 (대소문자 구분 없이 써서 나중에 서치하게)
                'foodId': food_id,  # 문서 ID와 동일
                'foodName': food_info.foodName,  # 검색한 음식명
                'data': {
                    'dishName': food_info.dishName,
                    'country': food_info.country,
                    'summary': food_info.summary,
                    'recommendations': food_info.recommendations,
                    'ingredients': food_info.ingredients,
                    'allergens': food_info.allergens,
                    'imageUrl': food_info.imageUrl,
                    'imageSource': food_info.imageSource,
                    'culturalBackground': food_info.culturalBackground
                },
                'timestamp': datetime.now(),
                'updatedAt': datetime.now()
            }
            
            # Firestore에 검색 결과 저장
            doc_ref = self.db.collection('search_results').document(doc_id)
            doc_ref.set(result_data)
            
            logger.info(f"검색 결과 저장 완료: {doc_id}")
            
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
