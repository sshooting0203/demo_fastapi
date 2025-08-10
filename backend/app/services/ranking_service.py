from ..db.firestore_client import firestore_client  # ✅ 래퍼 사용
from datetime import datetime, timedelta
from typing import List, Optional
from ..models.ranking import CountryRanking, TopFoodSnapshot

class RankingService:
    def __init__(self):
        self.db = firestore_client.db  # ✅ 래퍼의 db 사용
    
    async def get_top_foods(self, country: str, limit: int = 3) -> List[TopFoodSnapshot]:
        """국가별 상위 음식 조회 (MVP: 홈화면 Top 3용)"""
        try:
            ranking_ref = self.db.collection('country_rankings').document(country)
            ranking_doc = ranking_ref.get()
            
            if not ranking_doc.exists:
                return []
            
            ranking_data = ranking_doc.to_dict()
            top_foods = ranking_data.get('topFoods', [])
            
            # 상위 N개만 반환하고, 누락된 필드들을 추가
            result = []
            for food in top_foods[:limit]:
                # DB에서 가져온 데이터에 누락된 필드들을 추가
                food_data = {
                    'foodId': food.get('foodId', f"{country}_{food.get('foodName', 'unknown')}"),
                    'country': country,  # 현재 조회하는 국가로 설정
                    'foodName': food.get('foodName', '알 수 없는 음식'),
                    'searchCount': food.get('searchCount', 0),
                    'saveCount': food.get('saveCount', 0)
                }
                result.append(TopFoodSnapshot(**food_data))
            
            return result
        except Exception as e:
            print(f"랭킹 조회 오류: {str(e)}")
            return []

    async def update_country_ranking(self, country: str, food_query: str):
        """국가별 랭킹 업데이트 (MVP: 검색 시 간단하게)"""
        try:
            ranking_ref = self.db.collection('country_rankings').document(country)
            ranking_doc = ranking_ref.get()
            
            if ranking_doc.exists:
                ranking_data = ranking_doc.to_dict()
                top_foods = ranking_data.get('topFoods', [])
                
                # 기존 음식 검색
                existing_food = None
                for food in top_foods:
                    if food.get('foodName') == food_query:
                        existing_food = food
                        break
                
                if existing_food:
                    # 기존 음식이면 검색 횟수 증가
                    existing_food['searchCount'] = existing_food.get('searchCount', 0) + 1
                else:
                    # 새 음식이면 추가
                    new_food = {
                        'foodName': food_query,
                        'searchCount': 1,
                        'firstSearched': datetime.now().isoformat()
                    }
                    top_foods.append(new_food)
                
                # 검색 횟수 기준으로 정렬하고 상위 10개만 유지
                top_foods.sort(key=lambda x: x.get('searchCount', 0), reverse=True)
                top_foods = top_foods[:10]
                
                # 업데이트
                ranking_ref.update({
                    'topFoods': top_foods,
                    'lastUpdated': datetime.now().isoformat()
                })
            else:
                # 새 문서 생성
                new_ranking = {
                    'country': country,
                    'topFoods': [{
                        'foodName': food_query,
                        'searchCount': 1,
                        'firstSearched': datetime.now().isoformat()
                    }],
                    'createdAt': datetime.now().isoformat(),
                    'lastUpdated': datetime.now().isoformat()
                }
                ranking_ref.set(new_ranking)
                
        except Exception as e:
            print(f"랭킹 업데이트 오류: {str(e)}")
    
    async def cleanup_old_logs(self):
        """30일 이상 된 검색 로그 정리 (MVP: 간단하게)"""
        try:
            cutoff_date = datetime.now() - timedelta(days=30)
            
            # TTL 처리 - 간단하게
            old_logs = self.db.collection('search_logs').where('timestamp', '<', cutoff_date).stream()
            
            batch = self.db.batch()
            for log in old_logs:
                batch.delete(log.reference)
            
            if batch._mutations:
                batch.commit()
                
        except Exception as e:
            print(f"로그 정리 오류: {str(e)}")