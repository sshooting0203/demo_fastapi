import os
import json
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import random

load_dotenv()

def seed_dummy_data():
    """더미 데이터를 Firestore에 생성합니다 (모델 구조에 맞게 수정)"""
    try:
        # Firebase 초기화
        if not firebase_admin._apps:
            firebase_credentials = json.loads(os.getenv("FIREBASE_CREDENTIALS"))
            cred = credentials.Certificate(firebase_credentials)
            firebase_admin.initialize_app(cred)
            print("Firebase 초기화 완료")
        
        db = firestore.client()
        
        # ==================== 사용자 데이터 생성 ====================
        print("1. 사용자 데이터 생성 중...")
        
        # 모델 구조에 맞는 사용자 데이터
        dummy_users = [
            {
                "uid": "user_001",
                "displayName": "백산수님",
                "email": "test1@example.com",
                "allergies": ["EGG", "SHRIMP"],  # allergens와 일치
                "dietaryRestrictions": ["VEGETARIAN"],  # dietary_codes와 일치
                "currentCountry": "JP",
                "createdAt": datetime.now() - timedelta(days=30),
                "updatedAt": datetime.now()
            },
            {
                "uid": "user_002", 
                "displayName": "김철수님",
                "email": "test2@example.com",
                "allergies": ["MILK"],
                "dietaryRestrictions": [],
                "currentCountry": "KR",
                "createdAt": datetime.now() - timedelta(days=15),
                "updatedAt": datetime.now()
            },
            {
                "uid": "user_003",
                "displayName": "John Smith",
                "email": "test3@example.com",
                "allergies": ["PEANUT"],
                "dietaryRestrictions": ["VEGAN"],
                "currentCountry": "US",
                "createdAt": datetime.now() - timedelta(days=20),
                "updatedAt": datetime.now()
            }
        ]
        
        # 사용자 데이터 저장
        for user_data in dummy_users:
            user_ref = db.collection('users').document(user_data['uid'])
            user_data_copy = user_data.copy()
            user_data_copy['createdAt'] = user_data_copy['createdAt'].isoformat()
            user_data_copy['updatedAt'] = user_data_copy['updatedAt'].isoformat()
            user_ref.set(user_data_copy)
            print(f"   사용자 생성: {user_data['uid']} ({user_data['displayName']})")
        
        # ==================== 음식 정보 데이터 생성 ====================
        print("2. 음식 정보 데이터 생성 중...")
        
        # FoodInfo 모델 구조에 맞는 음식 데이터 (테스트용으로 검색/저장 횟수 포함)
        food_info_data = [
            {
                "foodId": "JP_tonkatsu",
                "foodInfo": {
                    "foodName": "돈카츠",
                    "dishName": "tonkatsu",
                    "country": "JP",
                    "summary": "돼지고기에 빵가루를 입혀 바삭하게 튀긴 일본의 대표 요리입니다.",
                    "recommendations": ["고기 좋아하는 사람", "튀김 요리 선호자"],
                    "ingredients": ["돼지고기", "빵가루", "계란", "밀가루"],
                    "allergens": ["PORK", "EGG", "WHEAT"],
                    "imageUrl": "https://picsum.photos/seed/food_JP_tonkatsu/800/500",
                    "imageSource": "일본 가정식 사진",
                    "culturalBackground": "서양 커틀릿의 영향을 받아 일본식으로 발전했습니다."
                }
            },
            {
                "foodId": "JP_ramen",
                "foodInfo": {
                    "foodName": "라멘",
                    "dishName": "ramen",
                    "country": "JP",
                    "summary": "육수와 밀면, 토핑이 조화를 이루는 일본 면 요리입니다.",
                    "recommendations": ["면 요리 애호가", "따뜻한 국물 선호자"],
                    "ingredients": ["밀면", "육수", "차슈", "계란", "파"],
                    "allergens": ["WHEAT", "EGG", "SOY", "PORK"],
                    "imageUrl": "https://picsum.photos/seed/food_JP_ramen/800/500",
                    "imageSource": "라멘 전문점 사진",
                    "culturalBackground": "중국 면 요리에서 파생되어 일본에서 독자적으로 발전했습니다."
                }
            },
            {
                "foodId": "JP_sushi",
                "foodInfo": {
                    "foodName": "초밥",
                    "dishName": "sushi",
                    "country": "JP",
                    "summary": "신선한 생선과 밥을 조합한 일본의 대표 요리입니다.",
                    "recommendations": ["생선 애호가", "건강식 선호자"],
                    "ingredients": ["생선", "밥", "와사비", "간장"],
                    "allergens": ["FISH", "SOY"],
                    "imageUrl": "https://picsum.photos/seed/food_JP_sushi/800/500",
                    "imageSource": "일본 초밥집 사진",
                    "culturalBackground": "에도 시대에 시작되어 현대까지 이어지는 전통 요리입니다."
                }
            },
            {
                "foodId": "KR_bibimbap",
                "foodInfo": {
                    "foodName": "비빔밥",
                    "dishName": "bibimbap",
                    "country": "KR",
                    "summary": "밥과 나물, 고추장, 계란 등을 비벼 먹는 한국 대표 한식입니다.",
                    "recommendations": ["채소 위주 식단", "한식 애호가"],
                    "ingredients": ["밥", "나물", "고추장", "계란", "참기름"],
                    "allergens": ["EGG", "SOY"],
                    "imageUrl": "https://picsum.photos/seed/food_KR_bibimbap/800/500",
                    "imageSource": "한식당 사진",
                    "culturalBackground": "지역마다 재료가 다르고 전주비빔밥이 특히 유명합니다."
                }
            },
            {
                "foodId": "KR_tteokbokki",
                "foodInfo": {
                    "foodName": "떡볶이",
                    "dishName": "tteokbokki",
                    "country": "KR",
                    "summary": "쌀떡을 매콤달콤한 고추장 소스로 볶아낸 길거리 간식입니다.",
                    "recommendations": ["매운맛 선호자", "간식 선호자"],
                    "ingredients": ["쌀떡", "고추장", "어묵", "대파"],
                    "allergens": ["SOY", "WHEAT"],
                    "imageUrl": "https://picsum.photos/seed/food_KR_tteokbokki/800/500",
                    "imageSource": "분식집 사진",
                    "culturalBackground": "대한민국 전역에서 사랑받는 대표적 분식 메뉴입니다."
                }
            },
            {
                "foodId": "KR_bulgogi",
                "foodInfo": {
                    "foodName": "불고기",
                    "dishName": "bulgogi",
                    "country": "KR",
                    "summary": "양념에 재운 소고기를 구워 먹는 한국의 대표 고기 요리입니다.",
                    "recommendations": ["고기 애호가", "단백질 보충"],
                    "ingredients": ["소고기", "간장", "설탕", "참기름", "깨"],
                    "allergens": ["BEEF", "SOY"],
                    "imageUrl": "https://picsum.photos/seed/food_KR_bulgogi/800/500",
                    "imageSource": "한식당 사진",
                    "culturalBackground": "고대부터 이어져 온 전통 요리로 현대에도 사랑받고 있습니다."
                }
            },
            {
                "foodId": "US_burger",
                "foodInfo": {
                    "foodName": "치즈버거",
                    "dishName": "cheeseburger",
                    "country": "US",
                    "summary": "번 사이에 소고기 패티와 치즈, 채소를 넣어 먹는 미국 대표 메뉴입니다.",
                    "recommendations": ["패스트푸드 선호자", "단백질 보충"],
                    "ingredients": ["번", "소고기 패티", "치즈", "양상추", "토마토"],
                    "allergens": ["WHEAT", "BEEF", "MILK", "TOMATO"],
                    "imageUrl": "https://picsum.photos/seed/food_US_burger/800/500",
                    "imageSource": "미국 패스트푸드 사진",
                    "culturalBackground": "20세기 미국에서 대중화되며 전 세계로 퍼졌습니다."
                }
            },
            {
                "foodId": "US_pizza",
                "foodInfo": {
                    "foodName": "피자",
                    "dishName": "pizza",
                    "country": "US",
                    "summary": "토마토 소스와 치즈, 다양한 토핑을 올려 구운 음식입니다.",
                    "recommendations": ["파티 음식", "치즈 애호가"],
                    "ingredients": ["밀가루 도우", "토마토 소스", "치즈", "페퍼로니"],
                    "allergens": ["WHEAT", "MILK", "TOMATO"],
                    "imageUrl": "https://picsum.photos/seed/food_US_pizza/800/500",
                    "imageSource": "뉴욕 스타일 피자 사진",
                    "culturalBackground": "이탈리아에서 유래했으나 미국식 스타일로 크게 확장되었습니다."
                }
            },
            {
                "foodId": "US_hotdog",
                "foodInfo": {
                    "foodName": "핫도그",
                    "dishName": "hotdog",
                    "country": "US",
                    "summary": "빵 사이에 소시지를 넣고 토핑을 올린 미국의 대표 길거리 음식입니다.",
                    "recommendations": ["길거리 음식 애호가", "간단한 식사"],
                    "ingredients": ["빵", "소시지", "겨자", "케첩", "양파"],
                    "allergens": ["WHEAT", "PORK"],
                    "imageUrl": "https://picsum.photos/seed/food_US_hotdog/800/500",
                    "imageSource": "뉴욕 길거리 사진",
                    "culturalBackground": "독일 이민자들이 가져온 소시지 문화가 미국에서 발전했습니다."
                }
            }
        ]
        
        # 메타데이터 컬렉션은 실제 검색/저장 시에만 생성되도록 변경
        print("2-1. 음식 메타데이터는 실제 검색/저장 시에 생성됩니다.")
        food_metadata = {}  # 메모리에서 추적용
        
        # ==================== 사용자별 저장된 음식 데이터 생성 ====================
        print("3. 사용자별 저장된 음식 데이터 생성 중...")
        
        # 각 사용자별로 랜덤하게 음식을 저장 (테스트용 저장 횟수 포함)
        for user_data in dummy_users:
            user_ref = db.collection('users').document(user_data['uid'])
            
            # 해당 사용자의 국가에 맞는 음식들만 선택
            user_country = user_data['currentCountry']
            available_foods = [item for item in food_info_data if item["foodInfo"]["country"] == user_country]
            
            # 랜덤하게 2-4개 음식 저장
            num_saved = random.randint(2, min(4, len(available_foods)))
            saved_foods = random.sample(available_foods, num_saved)
            
            for i, food_item in enumerate(saved_foods):
                food_info = food_item["foodInfo"]
                
                # 저장된 음식 데이터 구성
                saved_food_data = {
                    'savedAt': datetime.now() - timedelta(days=random.randint(1, 30)),
                    'foodInfo': food_info,
                    'notes': f"사용자 {user_data['displayName']}이 저장한 {food_info['foodName']}",
                    'rating': random.randint(3, 5)  # 3-5점 평점
                }
                
                # 문서 ID를 나라코드_영문음식명 형태로 생성 (중복 방지를 위해 인덱스 추가)
                doc_name = f"{food_info['country']}_{food_info['dishName']}"
                
                # users/{uid}/saved_foods 서브컬렉션에 저장
                saved_food_ref = user_ref.collection('saved_foods').document(doc_name)
                
                # datetime을 ISO 형식으로 변환
                saved_food_data_copy = saved_food_data.copy()
                saved_food_data_copy['savedAt'] = saved_food_data_copy['savedAt'].isoformat()
                
                saved_food_ref.set(saved_food_data_copy)
                
                                # 메타데이터 업데이트 (저장 횟수 증가)
                metadata_doc_name = f"{food_info['country']}_{food_info['dishName']}"
                if metadata_doc_name not in food_metadata:
                    # 메타데이터 구성
                    metadata = {
                        "country": food_info["country"],
                        "foodName": food_info["foodName"],
                        "dishName": food_info["dishName"],
                        "searchCount": 0,  # 검색 횟수
                        "saveCount": 1,    # 저장 횟수 (최초 저장이므로 1)
                        "lastSearched": None,  # 마지막 검색 시간
                        "updatedAt": datetime.now()
                    }
                    food_metadata[metadata_doc_name] = metadata
                    
                    # Firestore에 메타데이터 생성
                    metadata_ref = db.collection('food_metadata').document(metadata_doc_name)
                    metadata_copy = metadata.copy()
                    metadata_copy['updatedAt'] = metadata_copy['updatedAt'].isoformat()
                    metadata_ref.set(metadata_copy)
                    
                    print(f"   메타데이터 생성: {metadata_doc_name} ({food_info['foodName']})")
                else:
                    food_metadata[metadata_doc_name]['saveCount'] += 1
                    
                    # 메타데이터 업데이트
                    metadata_ref = db.collection('food_metadata').document(metadata_doc_name)
                    metadata_ref.update({
                        'saveCount': food_metadata[metadata_doc_name]['saveCount'],
                        'updatedAt': datetime.now().isoformat()
                    })
                
                print(f"   저장된 음식: {user_data['uid']} -> {food_info['foodName']} ({food_info['country']})")
        
        # ==================== 더미 검색 데이터 생성 ====================
        print("4. 더미 검색 데이터 생성 중...")
        
        # 실제 검색 패턴을 시뮬레이션하는 더미 검색 데이터 (테스트용 검색 횟수 포함)
        dummy_searches = [
            # 일본 음식 검색 (JP_tonkatsu: 5회, JP_ramen: 3회, JP_sushi: 2회)
            {"uid": "user_001", "query": "돈카츠", "country": "JP", "days_ago": 1, "count": 5},
            {"uid": "user_002", "query": "라멘", "country": "JP", "days_ago": 2, "count": 3},
            {"uid": "user_003", "query": "초밥", "country": "JP", "days_ago": 3, "count": 2},
            
            # 한국 음식 검색 (KR_bibimbap: 4회, KR_tteokbokki: 3회, KR_bulgogi: 2회)
            {"uid": "user_001", "query": "비빔밥", "country": "KR", "days_ago": 1, "count": 4},
            {"uid": "user_002", "query": "떡볶이", "country": "KR", "days_ago": 2, "count": 3},
            {"uid": "user_003", "query": "불고기", "country": "KR", "days_ago": 3, "count": 2},
            
            # 미국 음식 검색 (US_burger: 6회, US_pizza: 4회, US_hotdog: 2회)
            {"uid": "user_003", "query": "햄버거", "country": "US", "days_ago": 1, "count": 6},
            {"uid": "user_001", "query": "피자", "country": "US", "days_ago": 2, "count": 4},
            {"uid": "user_002", "query": "핫도그", "country": "US", "days_ago": 3, "count": 2}
        ]
        
        for search_data in dummy_searches:
            # 해당 음식 정보 찾기 (국가별로 매칭)
            food_info = next((item for item in food_info_data if item["foodInfo"]["country"] == search_data["country"]), None)
            
            if food_info:
                # 검색 횟수만큼 반복하여 검색 결과 생성
                for i in range(search_data['count']):
                    # 검색 결과 데이터 구성
                    search_result_data = {
                        'uid': search_data['uid'],
                        'query': search_data['query'],
                        'foodId': food_info['foodId'],
                        'foodInfo': food_info['foodInfo'],
                        'timestamp': datetime.now() - timedelta(days=search_data['days_ago'], hours=i)
                    }
                    
                    # 문서 ID를 나라코드_영문음식명 형태로 생성 (중복 방지)
                    doc_name = f"{food_info['foodInfo']['country']}_{food_info['foodInfo']['dishName']}"
                    
                    # search_results 컬렉션에 저장
                    search_ref = db.collection('search_results').document(doc_name)
                    
                    # datetime을 ISO 형식으로 변환
                    search_result_data_copy = search_result_data.copy()
                    search_result_data_copy['timestamp'] = search_result_data_copy['timestamp'].isoformat()
                    
                    search_ref.set(search_result_data_copy)
                    
                    # 메타데이터 업데이트 (검색 횟수 증가)
                    metadata_doc_name = f"{food_info['foodInfo']['country']}_{food_info['foodInfo']['dishName']}"
                    if metadata_doc_name not in food_metadata:
                        # 메타데이터 구성
                        metadata = {
                            "country": food_info["foodInfo"]["country"],
                            "foodName": food_info["foodInfo"]["foodName"],
                            "dishName": food_info["foodInfo"]["dishName"],
                            "searchCount": 1,  # 검색 횟수 (최초 검색이므로 1)
                            "saveCount": 0,    # 저장 횟수
                            "lastSearched": search_result_data_copy['timestamp'],  # 마지막 검색 시간
                            "updatedAt": datetime.now()
                        }
                        food_metadata[metadata_doc_name] = metadata
                        
                        # Firestore에 메타데이터 생성
                        metadata_ref = db.collection('food_metadata').document(metadata_doc_name)
                        metadata_copy = metadata.copy()
                        metadata_copy['updatedAt'] = metadata_copy['updatedAt'].isoformat()
                        metadata_ref.set(metadata_copy)
                        
                        print(f"   메타데이터 생성: {metadata_doc_name} ({food_info['foodInfo']['foodName']})")
                    else:
                        food_metadata[metadata_doc_name]['searchCount'] += 1
                        food_metadata[metadata_doc_name]['lastSearched'] = search_result_data_copy['timestamp']
                        
                        # 메타데이터 업데이트
                        metadata_ref = db.collection('food_metadata').document(metadata_doc_name)
                        metadata_ref.update({
                            'searchCount': food_metadata[metadata_doc_name]['searchCount'],
                            'lastSearched': food_metadata[metadata_doc_name]['lastSearched'],
                            'updatedAt': datetime.now().isoformat()
                        })
                
                print(f"   검색 데이터 생성: {search_data['uid']} -> {search_data['query']} ({search_data['country']}) x{search_data['count']}회")
        
        print("더미 데이터 생성 완료!")
        print("\n=== 생성된 데이터 구조 ===")
        print("1. users 컬렉션: 사용자 프로필 정보")
        print("2. users/{uid}/saved_foods 서브컬렉션: 각 사용자별 저장된 음식")
        print("3. search_results 컬렉션: 사용자 검색 기록 (TTL 7일)")
        print("4. food_metadata 컬렉션: 음식 통계 캐싱용 (문서명: JP_tonkatsu 형태, TTL 없음)")
        print("5. countries 컬렉션: 국가 정보 (setup_firestore.py에서 생성)")
        print("6. allergy_codes 컬렉션: 알레르기 코드 (setup_firestore.py에서 생성)")
        print("7. dietary_codes 컬렉션: 식단 제한 코드 (setup_firestore.py에서 생성)")
        print("8. country_rankings 컬렉션: 국가별 음식 랭킹 (setup_firestore.py에서 생성)")
        print("\n=== 테스트용 데이터 요약 ===")
        print("• JP: 돈카츠(검색5회), 라멘(검색3회), 초밥(검색2회)")
        print("• KR: 비빔밥(검색4회), 떡볶이(검색3회), 불고기(검색2회)")
        print("• US: 햄버거(검색6회), 피자(검색4회), 핫도그(검색2회)")
        print("• 각 음식별로 랜덤 저장 횟수 포함")
        print("\n홈 화면 Top 3 기능 테스트 가능!")
        
    except Exception as e:
        print(f"더미 데이터 생성 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    seed_dummy_data()
