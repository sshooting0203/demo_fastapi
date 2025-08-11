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
    - 검색 로그 저장 및 관리
    - 중복 검색 최적화
    - 음식 검색 통계 제공
    """
    
    def __init__(self):
        self.db = firestore_client.db
    
    async def _get_document_case_insensitive(self, collection_name: str, doc_id: str):
        """
        대소문자 구분 없이 Firestore 문서 조회
        
        Args:
            collection_name (str): 컬렉션 이름
            doc_id (str): 문서 ID
            
        Returns:
            DocumentSnapshot: 찾은 문서 또는 None
        """
        try:
            # 1. 정확한 ID로 먼저 시도
            doc = self.db.collection(collection_name).document(doc_id).get()
            if doc.exists:
                return doc
            
            # 2. 대소문자 구분 없이 검색
            docs = self.db.collection(collection_name).stream()
            for doc in docs:
                if doc.id.lower() == doc_id.lower():
                    logger.info(f"대소문자 구분 없이 문서 발견: {collection_name}/{doc.id} (원본 ID: {doc_id})")
                    return doc
            
            return None
            
        except Exception as e:
            logger.error(f"문서 조회 실패: {collection_name}/{doc_id} - {str(e)}")
            return None

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
            current_time = datetime.now()
            
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
                'timestamp': current_time,
                'updatedAt': current_time
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

    def _consolidate_foods_by_dish_name(self, foods: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        한국어 이름(dishName)이 같은 음식들을 통합하여 searchCount 합산
        
        Args:
            foods (List[Dict[str, Any]]): 원본 음식 목록
            
        Returns:
            List[Dict[str, Any]]: 통합된 음식 목록
        """
        if not foods:
            return []
        
        logger.info(f"통합 시작: 총 {len(foods)}개 음식")
        
        # 한국어 이름별로 그룹화 (dishName 사용)
        name_groups = {}
        
        for food in foods:
            korean_name = food.get('dishName', '').strip()
            if not korean_name:
                logger.warning(f"한국어 이름이 없는 음식: {food['doc_id']}")
                continue
            
            if korean_name not in name_groups:
                name_groups[korean_name] = []
            name_groups[korean_name].append(food)
        
        logger.info(f"한국어 이름별 그룹: {len(name_groups)}개 그룹")
        
        # 각 그룹을 통합
        consolidated = []
        
        for korean_name, group in name_groups.items():
            if len(group) == 1:
                # 그룹이 하나면 그대로 추가
                food = group[0]
                consolidated_food = {
                    'foodId': food['foodId'],
                    'foodName': food['foodName'],
                    'dishName': food['dishName'],
                    'searchCount': food['searchCount'],
                    'saveCount': food['saveCount'],
                    'lastSearched': food['lastSearched'],
                    'country': food['country'],
                    'consolidated_count': 1,
                    'original_docs': [food['doc_id']]
                }
            else:
                # 여러 개면 통합
                logger.info(f"통합 대상: '{korean_name}' - {len(group)}개 문서")
                for food in group:
                    logger.info(f"  - {food['doc_id']}: {food['dishName']} (searchCount: {food['searchCount']})")
                
                total_search_count = sum(f['searchCount'] for f in group)
                total_save_count = sum(f['saveCount'] for f in group)
                
                # searchCount가 가장 높은 것을 대표로 선택
                representative = max(group, key=lambda x: x['searchCount'])
                
                # 모든 원어 이름을 수집
                all_food_names = [f['foodName'] for f in group if f['foodName']]
                
                consolidated_food = {
                    'foodId': representative['foodId'],
                    'foodName': representative['foodName'],  # 대표 항목의 원어 이름
                    'dishName': korean_name,  # 한국어 이름
                    'searchCount': total_search_count,
                    'saveCount': total_save_count,
                    'lastSearched': representative['lastSearched'],
                    'country': representative['country'],
                    'consolidated_count': len(group),
                    'original_docs': [f['doc_id'] for f in group]
                }
            
            consolidated.append(consolidated_food)
        
        logger.info(f"통합 완료: {len(consolidated)}개 음식")
        return consolidated

    async def get_top_foods_by_country(self, country: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        국가별 상위 음식 조회 (food_metadata 기반, 한국어 이름 통합 적용)
        
        Args:
            country (str): 국가 코드 (예: "JP", "KR")
            limit (int): 조회할 음식 수 (기본값: 3)
            
        Returns:
            List[Dict[str, Any]]: 상위 음식 목록 (한국어 이름 통합 적용)
        """
        try:
            # food_metadata에서 해당 국가의 음식들을 searchCount 기준으로 정렬하여 더 많이 가져옴
            query = self.db.collection('food_metadata')\
                .where('country', '==', country)\
                .order_by('searchCount', direction=firestore.Query.DESCENDING)\
                .limit(limit * 3)  # 통합 후 필터링을 위해 더 많이 가져옴
            
            logging.info('query :  %s', query)

            docs = query.stream()
            all_foods = []
            
            for doc in docs:
                data = doc.to_dict()
                food_data = {
                    'doc_id': doc.id,
                    'foodId': doc.id,
                    'foodName': data.get('foodName', ''),
                    'dishName': data.get('dishName', ''),
                    'searchCount': data.get('searchCount', 0),
                    'saveCount': data.get('saveCount', 0),
                    'lastSearched': data.get('lastSearched'),
                    'country': data.get('country', '')
                }
                all_foods.append(food_data)
            
            # 한국어 이름 기준으로 통합
            consolidated_foods = self._consolidate_foods_by_dish_name(all_foods)
            
            # searchCount 기준으로 정렬하여 상위 limit개 반환
            top_foods = sorted(consolidated_foods, key=lambda x: x['searchCount'], reverse=True)[:limit]
            
            logger.info(f"국가 {country}의 상위 {len(top_foods)}개 음식 조회 완료 (한국어 이름 통합 적용)")
            return top_foods
            
        except Exception as e:
            logger.error(f"상위 음식 조회 오류: {str(e)}")
            return []

    async def find_existing_search_result(self, query: str, country: str = None) -> Optional[Dict[str, Any]]:
        """
        기존 검색 결과에서 동일한 쿼리로 검색된 결과가 있는지 확인
        
        Args:
            query (str): 검색 쿼리 (원어 음식명)
            country (str, optional): 국가 코드 (필터링용)
            
        Returns:
            Optional[Dict[str, Any]]: 기존 검색 결과 또는 None
        """
        try:
            logger.info(f"기존 검색 결과 검색: 쿼리='{query}', 국가='{country}'")
            
            # query 필드로 검색 (대소문자 구분 없이)
            query_ref = self.db.collection('search_results')
            
            if country:
                # 국가별로 필터링하여 검색
                logger.info(f"국가별 필터링 검색: {country}")
                docs = query_ref.where('data.country', '==', country).stream()
            else:
                # 전체에서 검색
                logger.info(f"전체 검색")
                docs = query_ref.stream()
            
            # query와 정확히 일치하거나 유사한 결과 찾기
            for doc in docs:
                data = doc.to_dict()
                stored_query = data.get('query', '').lower()
                current_query = query.lower()
                
                logger.debug(f"검색된 문서: {doc.id}, 저장된 쿼리: '{stored_query}', 현재 쿼리: '{current_query}'")
                
                # 정확한 일치 또는 유사한 음식명 확인
                if (stored_query == current_query or 
                    stored_query in current_query or 
                    current_query in stored_query):
                    logger.info(f"기존 검색 결과 발견: {doc.id} (쿼리: '{stored_query}' vs '{current_query}')")
                    return {
                        'doc_id': doc.id,
                        'data': data,
                        'is_existing': True
                    }
            
            logger.info(f"기존 검색 결과 없음: '{query}' (국가: {country})")
            return None
            
        except Exception as e:
            logger.error(f"기존 검색 결과 조회 실패: {str(e)}")
            return None

    async def personalize_search_result(self, search_result: Dict[str, Any], user_allergies: List[str], user_dietary: List[str]) -> Dict[str, Any]:
        """
        기존 검색 결과를 사용자 정보에 맞게 개인화
        
        Args:
            search_result (Dict[str, Any]): 기존 검색 결과
            user_allergies (List[str]): 사용자 알레르기 목록
            user_dietary (List[str]): 사용자 식단 제한
            
        Returns:
            Dict[str, Any]: 개인화된 검색 결과
        """
        try:
            logger.info(f"개인화 시작 - 사용자 알레르기: {user_allergies}, 식단제한: {user_dietary}")
            
            personalized_result = search_result.copy()
            data = search_result.get('data', {})
            
            # 1단계: 사용자 알레르기와 음식의 allergens 비교
            food_allergens = data.get('allergens', [])
            allergy_warnings = []
            
            for user_allergy in user_allergies:
                for food_allergen in food_allergens:
                    if user_allergy.lower() in food_allergen.lower():
                        allergy_warnings.append(food_allergen)
                        logger.info(f"알레르기 경고: {user_allergy} → {food_allergen}")
            
            # 2단계: 사용자 식단제한과 음식의 ingredients 비교
            food_ingredients = data.get('ingredients', [])
            dietary_warnings = []
            
            # 한국어 재료를 영어 코드로 변환하는 간단한 매핑
            # 이건 지금 시간 상 이렇게 매핑해서 처리함 -> 진짜 처리를 원하면 LLM 단에서 처리해야 할 듯?
            def convert_korean_to_english(ingredient):
                ingredient_lower = ingredient.lower()
                if any(word in ingredient_lower for word in ['계란', '달걀']):
                    return 'EGG'
                elif any(word in ingredient_lower for word in ['우유', '버터', '크림', '치즈', '유제품']):
                    return 'MILK'
                elif any(word in ingredient_lower for word in ['밀가루', '밀', '빵']):
                    return 'WHEAT'
                elif any(word in ingredient_lower for word in ['소고기', '쇠고기']):
                    return 'BEEF'
                elif any(word in ingredient_lower for word in ['돼지고기', '돼지']):
                    return 'PORK'
                elif any(word in ingredient_lower for word in ['닭고기', '닭']):
                    return 'CHICKEN'
                elif any(word in ingredient_lower for word in ['새우']):
                    return 'SHRIMP'
                elif any(word in ingredient_lower for word in ['땅콩']):
                    return 'PEANUT'
                elif any(word in ingredient_lower for word in ['콩', '대두', '두부']):
                    return 'SOY'
                return None
            
            # Firestore에서 사용자의 dietaryRestrictions에 해당하는 restrictedFoods 가져오기
            for restriction_code in user_dietary:
                doc = await self._get_document_case_insensitive('dietaryRestrictions', restriction_code)
                if doc:
                    restriction_data = doc.to_dict()
                    restricted_foods = restriction_data.get('restrictedFoods', [])
                    
                    logger.info(f"식단제한 {restriction_code}: 제한된 음식 {restricted_foods}")
                    
                    # 한국어 재료를 영어로 변환한 후 제한된 음식과 비교
                    for ingredient in food_ingredients:
                        english_code = convert_korean_to_english(ingredient)
                        if english_code and english_code in restricted_foods:
                            dietary_warnings.append(ingredient)
                            logger.info(f"식단제한 경고: {restriction_code} - {english_code} → {ingredient}")
                        # 이미 영어 코드인 경우도 체크
                        elif ingredient.upper() in restricted_foods:
                            dietary_warnings.append(ingredient)
                            logger.info(f"식단제한 경고: {restriction_code} - {ingredient} → {ingredient}")
            
            # 3단계: 간단한 경고 메시지 생성 -> 이거 프론트 단에서 경고 로그 찍기 편할 거라 생각해 ...
            allergy_message = ""
            if allergy_warnings:
                allergy_message = f"알러지 주의: {', '.join(set(allergy_warnings))}"
            dietary_message = ""
            if dietary_warnings:
                dietary_message = f"제한 음식: {', '.join(set(dietary_warnings))}"
            
            # 4단계: 개인화된 정보 추가
            personalized_result['personalized'] = {
                'allergy_warnings': allergy_warnings,
                'dietary_warnings': dietary_warnings,
                'allergy_message': allergy_message,
                'dietary_message': dietary_message,
                'is_safe': len(allergy_warnings) == 0 and len(dietary_warnings) == 0,
                'user_allergies': user_allergies,
                'user_dietary': user_dietary
            }
            
            logger.info(f"개인화 완료:")
            if allergy_message:
                logger.info(f"  {allergy_message}")
            if dietary_message:
                logger.info(f"  {dietary_message}")
            logger.info(f"  안전 여부: {personalized_result['personalized']['is_safe']}")
            
            return personalized_result
            
        except Exception as e:
            logger.error(f"검색 결과 개인화 실패: {str(e)}")
            return search_result

# 싱글톤 인스턴스
search_service = SearchService()
