from typing import Optional, Dict, List, Any
from ..db.firestore_client import firestore_client
from ..models.ranking import TopFoodSnapshot
from ..services.search_service import SearchService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class HomeService:
    """
    홈 화면 관련 서비스
    
    주요 기능:
    - 사용자 여행 국가 정보 조회
    - 홈 화면 표시용 데이터 제공 (사용자 요약 + 현재 국가 Top3)
    """

    def get_travel_country_info(self, uid: str) -> Optional[Dict]:
        """
        홈 화면 표시용 사용자 여행 국가 정보 조회
        
        Args:
            uid (str): 사용자 ID
            
        Returns:
            Optional[Dict]: 여행 국가 정보 {"countryCode", "countryName", "flag"} 또는 None
        """
        try:
            # 사용자 문서에서 여행 국가 코드 조회
            user_doc = firestore_client.db.collection("users").document(uid).get()
            if not user_doc.exists:
                return None

            code = (user_doc.to_dict() or {}).get("currentCountry")
            if not code:
                return None

            # 국가 코드로 상세 정보 조회
            country_doc = firestore_client.db.collection("country").document(code).get()
            if not country_doc.exists:
                return None

            country_data = country_doc.to_dict() or {}
            return {
                "countryCode": code,
                "countryName": country_data.get("nameKo") or country_data.get("name"),  # 한국어 우선 표시
                "flag": country_data.get("flag"),
            }
        except Exception as e:
            logger.error(f"여행 국가 정보 조회 실패: {str(e)}")
            return None
    
    async def get_top_foods(self, country: str, limit: int = 3) -> List[TopFoodSnapshot]:
        """
        국가별 상위 음식 조회 (홈 화면 Top 3용)
        
        Args:
            country (str): 국가 코드 (예: "JP", "KR")
            limit (int): 조회할 음식 수 (기본값: 3)
            
        Returns:
            List[TopFoodSnapshot]: 상위 음식 목록
        """
        try:
            # SearchService를 사용하여 food_metadata 기반 Top 음식 조회
            search_service = SearchService()
            top_foods_data = await search_service.get_top_foods_by_country(country, limit)
            
            # TopFoodSnapshot 모델로 변환
            result = []
            for food_data in top_foods_data:
                snapshot = TopFoodSnapshot(
                    foodId=food_data.get('foodId', ''),
                    country=food_data.get('country', country),
                    foodName=food_data.get('foodName', ''),
                    dishName=food_data.get('dishName', ''),
                    searchCount=food_data.get('searchCount', 0),
                    saveCount=food_data.get('saveCount', 0)
                )
                result.append(snapshot)
            
            logger.info(f"국가 {country}의 상위 {len(result)}개 음식 조회 완료")
            return result
            
        except Exception as e:
            logger.error(f"랭킹 조회 오류: {str(e)}")
            return []
    
    async def get_home_data(self, uid: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        홈 화면 데이터: 사용자 요약 + 현재 국가 Top3를 한 번에 반환
        
        Args:
            uid (str): 사용자 ID
            user_info (Dict[str, Any]): 기본 사용자 정보
            
        Returns:
            Dict[str, Any]: 홈 화면 데이터
                - user: 사용자 요약 정보
                - topFoods: 현재 국가 Top3 음식
        """
        try:
            # 현재 국가 정보 조회
            travel_country_info = self.get_travel_country_info(uid)
            
            # 사용자 정보에 국가 정보 추가
            if travel_country_info and travel_country_info.get("countryCode"):
                country_code = travel_country_info["countryCode"]
                user_info["currentCountry"] = country_code
                
                # 현재 국가 기반 Top 3 조회
                top_foods = await self.get_top_foods(country_code, 3)
                
                # 응답 데이터 정규화
                normalized_foods = []
                for food in top_foods:
                    normalized_food = {
                        "id": food.foodId,
                        "name": food.foodName,
                        "dishName": food.dishName,
                        "searchCount": food.searchCount,
                        "saveCount": food.saveCount
                    }
                    normalized_foods.append(normalized_food)
                
                return {
                    "user": user_info,
                    "topFoods": normalized_foods
                }
            else:
                # 국가 정보가 없는 경우
                return {
                    "user": user_info,
                    "topFoods": []
                }
                
        except Exception as e:
            logger.error(f"홈 데이터 조회 실패: {str(e)}")
            raise Exception(f"홈 데이터 조회 중 오류 발생: {str(e)}")

# 싱글톤 인스턴스
home_service = HomeService()
