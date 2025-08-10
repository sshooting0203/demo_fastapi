from typing import List, Optional
from app.models.ranking import TopFoodSnapshot
from app.models.user import User
from app.db.firestore_client import firestore_client
from datetime import datetime

class HomeService:    
    def get_user_travel_country(self, uid: str) -> Optional[str]:
        """사용자의 현재 여행 국가(국가코드; ex KR) 조회"""
        try:
            # Firestore에서 사용자 정보 조회 (동기 방식)
            user_doc = firestore_client.db.collection("users").document(uid).get()
            
            if user_doc.exists:
                user_data = user_doc.to_dict()
                return user_data.get("currentCountry")
            
            return None
        except Exception:
            return None
    
    def get_top_foods_by_country(self, country_code: str, limit: int = 3) -> List[TopFoodSnapshot]:
        """특정 국가(국가코드; ex KR)에서 검색 기록이 많은 순으로 상위 N개 음식 조회"""
        try:
            # Firestore에서 해당 국가의 상위 음식 조회 (동기 방식)
            # country_rankings/{country} 문서들에서 topFoods 필드 조회
            country_doc = firestore_client.db.collection("country_rankings").document(country_code).get()
            
            if country_doc.exists:
                data = country_doc.to_dict()
                top_foods = data.get("topFoods", [])
                
                # 검색 횟수 기준으로 정렬하고 상위 N개만 반환
                sorted_foods = sorted(top_foods, key=lambda x: x["searchCount"], reverse=True)[:limit]
                
                # TopFoodSnapshot(랭킹.py) 모델에 맞게 변환
                result = []
                for food in sorted_foods:
                    result.append(TopFoodSnapshot(
                        foodId=food["foodId"],
                        country=country_code,
                        foodName=food["foodName"],
                        searchCount=food["searchCount"],
                        saveCount=food["saveCount"]
                    ))
                return result
            
            return []
        except Exception:
            return []
    
    def get_country_code_by_name(self, country_name: str) -> Optional[str]:
        """국가명(ex 한국)으로 국가코드(ex KR) 조회"""
        try:
            # countries 컬렉션에서 국가명으로 검색
            countries_ref = firestore_client.db.collection("country")
            query = countries_ref.where("nameKo", "==", country_name).limit(1)
            docs = query.get()
            
            if docs:
                return docs[0].id
            
            # 영어명으로도 검색
            query = countries_ref.where("name", "==", country_name).limit(1)
            docs = query.get()
            
            if docs:
                return docs[0].id
            
            return None
        except Exception:
            return None
    
    def register_travel_country(self, uid: str, country_name: str) -> dict:
        """사용자의 여행 국가 등록"""
        try:
            # 국가명을 국가코드로 변환
            country_code = self.get_country_code_by_name(country_name)
            
            if not country_code: # DB에 없는 경우(지금 더미로 10개 조금 넣어둠)
                raise ValueError(f"지원하지 않는 국가입니다: {country_name}")
            
            # 사용자 문서 업데이트
            user_ref = firestore_client.db.collection("users").document(uid)
            user_ref.update({"currentCountry": country_code})
            
            return {
                "countryCode": country_code,
                "countryName": country_name
            }
        except Exception as e:
            raise e
    
    def get_travel_country_info(self, uid: str) -> Optional[dict]:
        """사용자의 여행 국가 정보 조회"""
        try:
            travel_country = self.get_user_travel_country(uid)
            
            if travel_country:
                # 국가 정보 조회
                country_doc = firestore_client.db.collection("country").document(travel_country).get()
                if country_doc.exists:
                    country_data = country_doc.to_dict()
                    return {
                        "countryCode": travel_country,
                        "countryName": country_data.get("nameKo"),
                        "flag": country_data.get("flag")
                    }
            
            return None
        except Exception:
            return None

    async def get_home_data(self, uid: str):
        """홈화면 데이터 조회"""
        # 1. 사용자 여행 국가 가져오기
        travel_country_info = self.get_travel_country_info(uid)
        
        if travel_country_info:
            country_code = travel_country_info['countryCode']
            # 2. 해당 국가의 상위 음식 가져오기 (기존 메서드 사용)
            top_foods = self.get_top_foods_by_country(country_code, limit=3)
        else:
            country_code = 'JP'
            top_foods = []
        
        return {
            "topFoods": top_foods,
            "country": country_code,
            "travelCountryInfo": travel_country_info
        }

# 서비스 인스턴스 생성
home_service = HomeService()
