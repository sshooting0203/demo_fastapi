from firebase_admin import firestore
from firebase_admin.firestore import Increment
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from ..models.search import SimpleSearchRequest, SimpleSearchResponse
from ..models.food import FoodInfo
from ..db.firestore_client import firestore_client
import logging
import re

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

    async def _save_search_result(self, uid: str, query: str, food_id: str, food_info: FoodInfo, target_language: str = None):
        """
        검색 결과를 Firestore에 저장 (AI 분석 결과 포함)
        
        Args:
            uid (str): 사용자 ID
            query (str): 검색 쿼리 (원어 음식명)
            food_id (str): 음식 ID ({나라코드두글자}_{foodName} 형태)
            food_info (FoodInfo): AI 분석된 음식 정보
            target_language (str): 번역 대상 언어 (예: "ko", "en")
        """
        try:
            # englishName 값 로깅
            english_name = getattr(food_info, 'englishName', '')
            logger.info(f"저장할 englishName: '{english_name}'")
            logger.info(f"target_language: '{target_language}'")
            
            # 타겟 언어가 제공된 경우, 해당 언어의 국가 코드로 ID 재생성
            if target_language and english_name:
                target_country_code = await self._get_country_code_from_language(target_language)
                english_name_normalized = await self._normalize_english_name(english_name)
                doc_id = f"{target_country_code}_{english_name_normalized}"
                logger.info(f"타겟 언어 기반 ID 생성: {target_country_code}_{english_name_normalized}")
            else:
                # 기존 방식 유지
                doc_id = food_id
                logger.info(f"기존 방식 ID 사용: {food_id}")
            
            result_data = {
                'uid': uid,
                'query': english_name or food_info.dishName or food_info.foodName,  # englishName 우선, 없으면 dishName, 없으면 원어
                'foodId': doc_id,  # 새로운 문서 ID
                'foodName': food_info.foodName,  # 검색한 음식명
                'data': {
                    'dishName': food_info.dishName,
                    'country': food_info.country,
                    'englishName': english_name,  # englishName 필드 추가
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
    
    async def _update_food_search_count(self, food_info: FoodInfo, target_language: str = None):
        """
        검색 시 해당 음식의 카운트를 업데이트 (food_metadata 기반)
        메타데이터가 없으면 새로 생성
        
        Args:
            food_info (FoodInfo): 음식 정보
            target_language (str): 번역 대상 언어
        """
        try:
            country = food_info.country
            food_name = food_info.foodName
            english_name = getattr(food_info, 'englishName', '')
            
            logger.info(f"메타데이터 업데이트 시작 - country: {country}, food_name: {food_name}, english_name: '{english_name}'")
            
            # 1. englishName으로 기존 메타데이터 찾기 (가장 정확한 방법)
            if english_name:
                target_country_code = await self._get_country_code_from_language(target_language) if target_language else country
                english_name_normalized = await self._normalize_english_name(english_name)
                expected_doc_id = f"{target_country_code}_{english_name_normalized}"
                
                logger.info(f"englishName 기반 메타데이터 검색: {expected_doc_id}")
                
                # 해당 ID로 직접 조회
                doc = self.db.collection('food_metadata').document(expected_doc_id).get()
                if doc.exists:
                    # 검색 횟수 증가 및 마지막 검색 시간 업데이트
                    doc.reference.update({
                        'searchCount': Increment(1),
                        'lastSearched': datetime.now().isoformat(),
                        'updatedAt': datetime.now().isoformat()
                    })
                    logger.info(f"음식 카운트 업데이트 완료: {expected_doc_id}")
                    return
                else:
                    logger.info(f"englishName 기반 메타데이터 없음: {expected_doc_id}")
            
            # 2. 기존 방식으로 찾기 (country + foodName으로 검색)
            logger.info(f"기존 방식으로 메타데이터 검색: country={country}, foodName={food_name}")
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
                logger.info(f"음식 카운트 업데이트 완료: {doc.id}")
                return
            
            # 3. 메타데이터가 없는 경우 새로 생성
            logger.info(f"새로운 음식 메타데이터 생성: {country} - {food_name}")
            
            # 문서 ID 생성 (타겟 언어 기반)
            if target_language and english_name:
                target_country_code = await self._get_country_code_from_language(target_language)
                english_name_normalized = await self._normalize_english_name(english_name)
                doc_id = f"{target_country_code}_{english_name_normalized}"
                logger.info(f"타겟 언어 기반 메타데이터 ID 생성: {doc_id}")
            else:
                # 기존 방식
                dish_name = food_name.lower().replace(' ', '_')
                doc_id = f"{country}_{dish_name}"
                logger.info(f"기존 방식 메타데이터 ID 생성: {doc_id}")
            
            # 메타데이터 생성
            metadata = {
                'country': country,
                'foodName': food_name,
                'dishName': getattr(food_info, 'dishName', food_name),
                'englishName': english_name,  # englishName 필드 추가
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
        새로운 문서명 로직: {국가코드}_{englishName} 형태
        
        Args:
            country (str): 국가 코드 (예: "JP", "KR")
            limit (int): 조회할 음식 수 (기본값: 3)
            
        Returns:
            List[Dict[str, Any]]: 상위 음식 목록 (foodId, foodName, dishName, searchCount, saveCount 포함)
        """
        try:
            logger.info(f"국가 {country}의 상위 {limit}개 음식 조회 시작")
            
            # 1차 시도: country 필드로 인덱스 기반 검색 (더 효율적)
            try:
                query = self.db.collection('food_metadata')\
                    .where('country', '==', country)\
                    .order_by('searchCount', direction=firestore.Query.DESCENDING)\
                    .limit(limit)
                
                docs = query.stream()
                top_foods = []
                
                for doc in docs:
                    data = doc.to_dict()
                    food_data = {
                        'foodId': doc.id,  # 문서 ID (예: KR_hotpot)
                        'foodName': data.get('foodName', ''),  # 원어 이름
                        'dishName': data.get('dishName', ''),  # 번역된 이름
                        'englishName': data.get('englishName', ''),  # 영어 이름
                        'searchCount': data.get('searchCount', 0),
                        'saveCount': data.get('saveCount', 0),
                        'lastSearched': data.get('lastSearched'),
                        'country': data.get('country', '')
                    }
                    top_foods.append(food_data)
                
                if top_foods:
                    logger.info(f"인덱스 기반 검색으로 국가 {country}의 상위 {len(top_foods)}개 음식 조회 완료")
                    return top_foods
                    
            except Exception as e:
                logger.warning(f"인덱스 기반 검색 실패, 문서명 기반 검색으로 폴백: {str(e)}")
            
            # 2차 시도: 문서명 기반 검색 (폴백)
            logger.info(f"문서명 기반 검색으로 폴백")
            docs = self.db.collection('food_metadata').stream()
            top_foods = []
            
            for doc in docs:
                # 문서명에서 국가코드 추출 (예: "KR_hotpot" -> "KR")
                doc_id = doc.id
                if '_' in doc_id:
                    doc_country = doc_id.split('_')[0]
                    
                    # 해당 국가의 음식인지 확인
                    if doc_country == country:
                        data = doc.to_dict()
                        food_data = {
                            'foodId': doc.id,  # 문서 ID (예: KR_hotpot)
                            'foodName': data.get('foodName', ''),  # 원어 이름
                            'dishName': data.get('dishName', ''),  # 번역된 이름
                            'englishName': data.get('englishName', ''),  # 영어 이름
                            'searchCount': data.get('searchCount', 0),
                            'saveCount': data.get('saveCount', 0),
                            'lastSearched': data.get('lastSearched'),
                            'country': data.get('country', '')
                        }
                        top_foods.append(food_data)
            
            # searchCount 기준으로 정렬하고 상위 limit개 선택
            top_foods.sort(key=lambda x: x['searchCount'], reverse=True)
            top_foods = top_foods[:limit]
            
            logger.info(f"문서명 기반 검색으로 국가 {country}의 상위 {len(top_foods)}개 음식 조회 완료")
            return top_foods
            
        except Exception as e:
            logger.error(f"상위 음식 조회 오류: {str(e)}")
            return []

    async def find_existing_search_result(self, query: str, target_language: str = None) -> Optional[Dict[str, Any]]:
        """
        기존 검색 결과에서 동일한 쿼리로 검색된 결과가 있는지 확인
        search_results 문서명을 기반으로 검색
        
        Args:
            query (str): 검색 쿼리 (원어 음식명 또는 englishName)
            target_language (str): 번역 대상 언어 (문서명 생성용)
            
        Returns:
            Optional[Dict[str, Any]]: 기존 검색 결과 또는 None
        """
        try:
            logger.info(f"기존 검색 결과 검색: 쿼리='{query}', 타겟언어='{target_language}'")
            
            # 1. englishName이 있는 경우, 타겟 언어 기반 문서명으로 검색
            if target_language:
                # query가 englishName인지 확인 (영어인지 체크)
                is_english = bool(re.match(r'^[a-zA-Z\s\-_]+$', query))
                
                if is_english:
                    # query가 이미 englishName인 경우
                    english_name = query
                    logger.info(f"query가 englishName으로 확인됨: {english_name}")
                else:
                    # query가 원어인 경우, 문서 내부에서 englishName을 찾아야 함
                    logger.info(f"query가 원어로 확인됨, 문서 내부 검색으로 전환: {query}")
                    return await self._find_by_original_name(query, target_language)
                
                target_country_code = await self._get_country_code_from_language(target_language)
                english_name_normalized = await self._normalize_english_name(english_name)
                expected_doc_id = f"{target_country_code}_{english_name_normalized}"
                
                logger.info(f"타겟 언어 기반 문서명으로 검색: {expected_doc_id}")
                
                # 해당 문서명으로 직접 조회
                doc = self.db.collection('search_results').document(expected_doc_id).get()
                if doc.exists:
                    data = doc.to_dict()
                    logger.info(f"기존 검색 결과 발견 (문서명 기반): {expected_doc_id}")
                    return {
                        'doc_id': doc.id,
                        'data': data,
                        'is_existing': True
                    }
                else:
                    logger.info(f"문서명 기반 검색 결과 없음: {expected_doc_id}")
            
            # 2. englishName 기반으로 더 정확한 검색
            logger.info(f"englishName 기반 정확 검색 시도")
            query_ref = self.db.collection('search_results')
            docs = query_ref.stream()
            
            # englishName으로 정확한 매칭 찾기
            for doc in docs:
                data = doc.to_dict()
                stored_english_name = data.get('data', {}).get('englishName', '').lower()
                current_english_name = query.lower()
                
                # englishName이 정확히 일치하는 경우
                if stored_english_name == current_english_name:
                    logger.info(f"기존 검색 결과 발견 (englishName 정확 일치): {doc.id}")
                    return {
                        'doc_id': doc.id,
                        'data': data,
                        'is_existing': True
                    }
            
            # 3. 기존 방식으로도 검색 (query 필드 기반, 폴백)
            logger.info(f"query 필드 기반 검색 시도 (폴백)")
            docs = query_ref.stream()
            
            # query와 정확히 일치하거나 유사한 결과 찾기
            for doc in docs:
                data = doc.to_dict()
                stored_query = data.get('query', '').lower()
                current_query = query.lower()
                
                # englishName이나 dishName도 확인
                english_name = data.get('data', {}).get('englishName', '').lower()
                dish_name = data.get('data', {}).get('dishName', '').lower()
                
                logger.debug(f"검색된 문서: {doc.id}, 저장된 쿼리: '{stored_query}', 현재 쿼리: '{current_query}'")
                logger.debug(f"englishName: '{english_name}', dishName: '{dish_name}'")
                
                # 정확한 일치 또는 유사한 음식명 확인 (여러 필드 비교)
                if (stored_query == current_query or 
                    english_name == current_query or
                    dish_name == current_query or
                    stored_query in current_query or 
                    current_query in stored_query or
                    english_name in current_query or
                    current_query in english_name or
                    dish_name in current_query or
                    current_query in dish_name):
                    logger.info(f"기존 검색 결과 발견 (query 필드 기반): {doc.id} (쿼리: '{stored_query}' vs '{current_query}')")
                    return {
                        'doc_id': doc.id,
                        'data': data,
                        'is_existing': True
                    }
            
            logger.info(f"기존 검색 결과 없음: '{query}' (타겟언어: {target_language})")
            return None
            
        except Exception as e:
            logger.error(f"기존 검색 결과 조회 실패: {str(e)}")
            return None
    
    async def _find_by_original_name(self, original_name: str, target_language: str) -> Optional[Dict[str, Any]]:
        """
        원어 음식명으로 저장된 문서를 찾아서 englishName을 추출하여 검색
        
        Args:
            original_name (str): 원어 음식명 (예: たこ焼き)
            target_language (str): 타겟 언어
            
        Returns:
            Optional[Dict[str, Any]]: 기존 검색 결과 또는 None
        """
        try:
            logger.info(f"원어 '{original_name}'으로 저장된 문서 검색")
            
            # search_results에서 원어 음식명이 포함된 문서 찾기
            docs = self.db.collection('search_results').stream()
            
            for doc in docs:
                data = doc.to_dict()
                stored_food_name = data.get('foodName', '').lower()
                stored_dish_name = data.get('data', {}).get('dishName', '').lower()
                
                # 원어 음식명과 일치하는 문서 찾기
                if (original_name.lower() == stored_food_name or 
                    original_name.lower() == stored_dish_name):
                    
                    # 해당 문서에서 englishName 추출
                    english_name = data.get('data', {}).get('englishName', '')
                    if english_name:
                        logger.info(f"원어 '{original_name}'에 해당하는 englishName 발견: {english_name}")
                        
                        # englishName으로 다시 검색
                        target_country_code = await self._get_country_code_from_language(target_language)
                        english_name_normalized = await self._normalize_english_name(english_name)
                        expected_doc_id = f"{target_country_code}_{english_name_normalized}"
                        
                        # 해당 문서명으로 조회
                        target_doc = self.db.collection('search_results').document(expected_doc_id).get()
                        if target_doc.exists:
                            target_data = target_doc.to_dict()
                            logger.info(f"englishName 기반 검색 결과 발견: {expected_doc_id}")
                            return {
                                'doc_id': target_doc.id,
                                'data': target_data,
                                'is_existing': True
                            }
            
            logger.info(f"원어 '{original_name}'에 해당하는 englishName 기반 문서를 찾을 수 없음")
            return None
            
        except Exception as e:
            logger.error(f"원어 기반 검색 실패: {str(e)}")
            return None

    async def personalize_search_result(self, search_result: Dict[str, Any], user_allergies: List[str], user_dietary: List[str]) -> Dict[str, Any]:
        """
        기존 검색 결과를 사용자 정보에 맞게 개인화
        
        Args:
            search_result (Dict[str, Any]): 기존 검색 결과
            user_allergies (List[str]): 사용자 알레르기 목록
            user_dietary (List[str]): 사용자 식단 제한 목록
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
            
            # 2단계: 사용자 식단제한과 음식의 dietaryRestrictions 비교
            food_dietary_restrictions = data.get('dietaryRestrictions', [])
            dietary_warnings = []  # 제한사항 코드를 담을 배열
            matched_restriction_codes = set()  # 매칭된 제한사항 코드 추적
            
            logger.info(f"사용자 식단제한: {user_dietary}")
            logger.info(f"음식 식단제한: {food_dietary_restrictions}")
            logger.info(f"전체 데이터: {data}")
            
            # 사용자의 dietaryRestrictions와 음식의 dietaryRestrictions를 포함 관계로 비교
            for user_restriction in user_dietary:
                for food_restriction in food_dietary_restrictions:
                    user_lower = user_restriction.lower()
                    food_lower = food_restriction.lower()
                    
                    logger.info(f"비교: {user_lower} vs {food_lower}")
                    
                    # 베지터리언이면 비건도 포함 (비건이 더 넓은 범위)
                    if user_lower == "vegan" and food_lower == "vegetarian":
                        matched_restriction_codes.add(user_restriction)  # 매칭된 제한사항 기록
                        matched_restriction_codes.add(food_restriction)  # 베지터리언도 추가
                        dietary_warnings.append(user_restriction)  # VEGAN 추가
                        dietary_warnings.append(food_restriction)  # VEGETARIAN 추가
                        logger.info(f"식단제한 매칭 (비건 포함): {user_restriction} → {food_restriction}")
                    # 정확히 일치하는 경우
                    elif user_lower == food_lower:
                        matched_restriction_codes.add(user_restriction)  # 매칭된 제한사항 기록
                        dietary_warnings.append(user_restriction)  # 제한사항 코드 추가
                        logger.info(f"식단제한 매칭 (정확 일치): {user_restriction} → {food_restriction}")
                    else:
                        logger.info(f"매칭 안됨: {user_restriction} vs {food_restriction}")
            
            logger.info(f"최종 매칭된 제한사항: {matched_restriction_codes}")
            logger.info(f"식단제한 경고 코드: {dietary_warnings}")
            
            # 3단계: 간단한 경고 메시지 생성
            allergy_message = ""
            if allergy_warnings:
                allergy_message = f"알러지 주의: {', '.join(set(allergy_warnings))}"
            
            dietary_message = ""
            if matched_restriction_codes:
                # 매칭된 dietaryRestrictions 문서명들을 포함한 메시지 생성
                matched_restrictions_list = sorted(list(matched_restriction_codes))
                dietary_message = f"식단제한 주의 ({', '.join(matched_restrictions_list)})"
            else:
                # 매칭된 항목이 없는 경우
                dietary_message = "식단제한 관련 주의사항 없음"
            
            # 4단계: 개인화된 정보 추가
            personalized_result['personalized'] = {
                'allergy_warnings': list(set(allergy_warnings)),  # 중복 제거
                'dietary_warnings': list(set(dietary_warnings)),  # 중복 제거된 제한사항 코드 배열
                'allergy_message': allergy_message,
                'dietary_message': dietary_message,
                'is_safe': len(allergy_warnings) == 0 and len(matched_restriction_codes) == 0,
                'user_allergies': user_allergies,
                'user_dietary': user_dietary
            }
            
            logger.info(f"개인화 완료:")
            logger.info(f"  알레르기 경고 수: {len(set(allergy_warnings))}")
            if allergy_warnings:
                logger.info(f"  알레르기 경고: {', '.join(set(allergy_warnings))}")
            
            logger.info(f"  식단제한 매칭 수: {len(matched_restriction_codes)}")
            if matched_restriction_codes:
                logger.info(f"  매칭된 제한사항: {', '.join(sorted(matched_restriction_codes))}")
            else:
                logger.info(f"  매칭된 제한사항: 없음")
            
            logger.info(f"  안전 여부: {personalized_result['personalized']['is_safe']}")
            
            return personalized_result
            
        except Exception as e:
            logger.error(f"검색 결과 개인화 실패: {str(e)}")
            return search_result

    async def _get_country_code_from_language(self, language_code: str) -> str:
        """
        언어 코드로 국가 코드 찾기 (country 컬렉션 쿼리)
        languages 배열의 0번 인덱스만 고려
        
        Args:
            language_code (str): 언어 코드 (예: "ko", "en", "zh")
            
        Returns:
            str: 국가 코드 (예: "KR", "US", "CN") 또는 "UN" (찾을 수 없는 경우)
        """
        try:
            # country 컬렉션의 모든 문서를 가져와서 languages 배열의 0번 인덱스 확인
            docs = self.db.collection('country').stream()
            
            for doc in docs:
                country_data = doc.to_dict()
                languages = country_data.get('languages', [])
                
                # languages 배열이 있고, 0번 인덱스가 해당 언어와 일치하는지 확인
                if languages and len(languages) > 0 and languages[0].lower() == language_code.lower():
                    country_code = country_data.get('code', '')
                    if country_code:
                        logger.info(f"언어 {language_code} -> 국가 {country_code} 매핑 완료 (0번 인덱스)")
                        return country_code
            
            logger.warning(f"언어 {language_code}에 해당하는 국가를 찾을 수 없음 (0번 인덱스)")
            return "UN"
            
        except Exception as e:
            logger.error(f"언어 코드로 국가 찾기 실패: {str(e)}")
            return "UN"

    async def _normalize_english_name(self, english_name: str) -> str:
        """
        영어 이름을 정규화 (띄어쓰기 제거, 소문자 변환)
        --> 이거 지금 food_metadata와 search_results 문서명 작성에 사용하고 있음
        
        Args:
            english_name (str): 영어 이름
            
        Returns:
            str: 정규화된 이름
        """
        if not english_name:
            return ""
        # 띄어쓰기, 하이픈, 언더스코어 제거하고 소문자로 변환
        normalized = english_name.replace(" ", "").replace("-", "").replace("_", "").lower()
        return normalized

# 싱글톤 인스턴스
search_service = SearchService()
