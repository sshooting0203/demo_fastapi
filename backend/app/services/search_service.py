from firebase_admin import firestore
from datetime import datetime, timedelta
from typing import List, Optional
from app.models.search import SimpleSearchRequest, SimpleSearchResponse
from app.models.ranking import CountryRanking, TopFoodSnapshot
from app.models.food import FoodInfo
from app.db.firestore_client import firestore_client
from app.ai.food_analyzer import _to_thread, extract_user_constraints, get_user_profile, analyze_one_async
import uuid, logging

logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self):
        self.db = firestore_client.db
    
    async def search_food(self, request: SimpleSearchRequest, uid: Optional[str] = None) -> SimpleSearchResponse:
        """
        음식 검색 (MVP: OCR/번역 결과를 AI 음식 설명으로 변환)
        """
        user = await _to_thread(get_user_profile, uid)
        cons = extract_user_constraints(user or {})
        data = await analyze_one_async(cons, request)
        logging.info('data!!! : %s',data)
        food_id = f"{request.country}_{request.food_name}" 

        # 응답 생성 (AI 음식 설명 포함)
        return SimpleSearchResponse(
            foodId=food_id,
            foodInfo=FoodInfo(
                foodName=request.food_name,
                dishName=data.get("dishName"),
                country=request.country,
                summary=data.get("summary"),
                recommendations=data.get("recommendedFor"),
                ingredients=data.get("ingredients"),
                allergens=data.get("allergens"),
                imageUrl=data.get("url"),
                imageSource=data.get("imgSrc"),
                culturalBackground=data.get("originCulture")
            ),
            isSaved=False,
            searchCount=await self._get_search_count(food_id)
        )
    
    async def log_search(self, uid: str, query: str, country: str):
        """검색 로그 저장 (MVP: 간단하게)"""
        try:
            log_id = str(uuid.uuid4())
            log_data = {
                'logId': log_id,
                'uid': uid,
                'country': country,
                'query': query,
                'timestamp': datetime.now(),
                'searchType': 'USER_SEARCH'
            }
            
            # Firestore에 저장
            doc_ref = self.db.collection('search_logs').document(log_id)
            doc_ref.set(log_data)
            
        except Exception as e:
            print(f"검색 로그 저장 오류: {str(e)}")
    
    async def _get_search_count(self, food_id: str) -> int:
        """음식 검색 횟수 조회 (MVP: 간단하게)"""
        try:
            logs = self.db.collection('search_logs').where('foodId', '==', food_id).stream()
            count = sum(1 for _ in logs)
            return count
        except Exception as e:
            print(f"검색 횟수 조회 오류: {str(e)}")
            return 0
    
    async def cleanup_old_search_logs(self, days: int = 30):
        """오래된 검색 로그 정리 (MVP: 간단하게)"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            old_logs = self.db.collection('search_logs').where('timestamp', '<', cutoff_date).stream()
            
            batch = self.db.batch()
            for log in old_logs:
                batch.delete(log.reference)
            
            if batch._mutations:
                batch.commit()
                
        except Exception as e:
            print(f"검색 로그 정리 오류: {str(e)}")
