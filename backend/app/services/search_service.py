from firebase_admin import firestore
from datetime import datetime, timedelta
from typing import List, Optional
from ..models.search import SimpleSearchRequest, SimpleSearchResponse
from ..models.ranking import CountryRanking, TopFoodSnapshot
from ..models.food import FoodInfo
from ..db.firestore_client import firestore_client
import uuid

class SearchService:
    def __init__(self):
        self.db = firestore_client.db
    
    async def search_food(self, request: SimpleSearchRequest, uid: Optional[str] = None) -> SimpleSearchResponse:
        """
        음식 검색 (MVP: OCR/번역 결과를 AI 음식 설명으로 변환)
        """
        # 임시 구현 (AI 로직은 나중에 연결)
        food_id = f"JP_{request.query[:5]}"  # 국가_음식명 형태로 ID 생성
        
        # 응답 생성 (AI 음식 설명 포함)
        return SimpleSearchResponse(
            foodId=food_id,
            foodInfo=FoodInfo(
                foodName=request.query,
                dishName=request.query,
                country="JP",
                summary="이 음식에 대한 AI 설명이 여기에 표시됩니다.",
                recommendations=["음식을 좋아하는 사람"],
                ingredients=["재료1", "재료2"],
                allergens=["알러지 정보"],
                imageUrl="https://example.com/placeholder.jpg",
                imageSource="AI 생성",
                culturalBackground="문화/역사 정보"
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
