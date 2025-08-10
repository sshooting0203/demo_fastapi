import os
import json
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta

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
                "allergies": ["EGG", "SHRIMP"],  # allergy_codes와 일치
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
        
        # FoodInfo 모델 구조에 맞는 음식 데이터
        food_info_data = [
            {
                "foodId": "JP_tonkatsu",
                "foodInfo": {
                    "foodName": "돈카츠",
                    "dishName": "とんかつ",
                    "country": "JP",
                    "summary": "돈카츠는 돼지고기를 빵가루를 묻혀 튀긴 일본의 대표적인 요리입니다.",
                    "recommendations": ["고기 좋아하는 사람", "튀김 요리 선호자"],
                    "ingredients": ["돼지고기", "빵가루", "계란", "밀가루"],
                    "allergens": ["WHEAT", "EGG"],  # allergy_codes와 일치
                    "imageUrl": "https://example.com/tonkatsu.jpg",
                    "imageSource": "일본 요리 사진",
                    "culturalBackground": "일본 메이지 시대에 서양의 커틀릿을 참고하여 만들어진 요리입니다."
                }
            },
            {
                "foodId": "JP_ramen",
                "foodInfo": {
                    "foodName": "라멘",
                    "dishName": "ラーメン",
                    "country": "JP",
                    "summary": "라멘은 일본의 대표적인 면 요리로, 다양한 스프와 토핑으로 구성됩니다.",
                    "recommendations": ["면 요리 애호가", "따뜻한 국물 요리 선호자"],
                    "ingredients": ["면", "돼지뼈 스프", "차슈", "계란", "김"],
                    "allergens": ["WHEAT", "EGG"],  # allergy_codes와 일치
                    "imageUrl": "https://example.com/ramen.jpg",
                    "imageSource": "일본 라멘 사진",
                    "culturalBackground": "중국에서 유래했지만 일본에서 독자적으로 발전한 요리입니다."
                }
            },
            {
                "foodId": "KR_bibimbap",
                "foodInfo": {
                    "foodName": "비빔밥",
                    "dishName": "비빔밥",
                    "country": "KR",
                    "summary": "비빔밥은 한국의 대표적인 한식으로, 다양한 채소와 고기를 밥과 함께 비벼 먹는 요리입니다.",
                    "recommendations": ["건강한 식사 선호자", "채소 요리 애호가"],
                    "ingredients": ["밥", "당근", "오이", "시금치", "고기", "고추장"],
                    "allergens": ["TOMATO"],  # allergy_codes와 일치 (고추장에 토마토 성분)
                    "imageUrl": "https://example.com/bibimbap.jpg",
                    "imageSource": "한국 비빔밥 사진",
                    "culturalBackground": "조선시대 궁중 요리에서 유래했으며, 제철 음식을 한 그릇에 담아 먹는 지혜로운 요리입니다."
                }
            },
            {
                "foodId": "US_burger",
                "foodInfo": {
                    "foodName": "치즈버거",
                    "dishName": "Cheeseburger",
                    "country": "US",
                    "summary": "치즈버거는 미국의 대표적인 패스트푸드로, 빵, 패티, 치즈, 채소로 구성됩니다.",
                    "recommendations": ["패스트푸드 애호가", "고기 요리 선호자"],
                    "ingredients": ["번", "소고기 패티", "치즈", "양상추", "토마토", "양파"],
                    "allergens": ["WHEAT", "MILK"],  # allergy_codes와 일치
                    "imageUrl": "https://example.com/burger.jpg",
                    "imageSource": "미국 버거 사진",
                    "culturalBackground": "20세기 초 미국에서 시작된 패스트푸드 문화의 상징적인 요리입니다."
                }
            }
        ]
        
        # ==================== 사용자별 저장된 음식 데이터 생성 ====================
        print("3. 사용자별 저장된 음식 데이터 생성 중...")
        
        # 각 사용자별로 다른 음식을 저장하도록 구성
        user_foods_mapping = {
            "user_001": ["JP_tonkatsu", "JP_ramen"],  # 일본 여행자
            "user_002": ["KR_bibimbap"],              # 한국 사용자
            "user_003": ["US_burger"]                  # 미국 사용자
        }
        
        for user_uid, food_ids in user_foods_mapping.items():
            for food_id in food_ids:
                # 해당 음식 정보 찾기
                food_info = next((item for item in food_info_data if item["foodId"] == food_id), None)
                if not food_info:
                    continue
                
                # SavedFood 모델 구조에 맞게 데이터 구성
                saved_food_data = {
                    "id": food_id,  # 음식 ID를 문서 ID로 사용
                    "userImageUrl": f"https://example.com/user_{user_uid}_{food_id}.jpg",
                    "foodInfo": food_info["foodInfo"],
                    "restaurantName": f"{food_info['foodInfo']['country']}_restaurant",
                    "savedAt": datetime.now() - timedelta(days=len(food_ids))
                }
                
                # users/{uid}/saved_foods 서브컬렉션에 저장
                saved_food_ref = db.collection('users').document(user_uid).collection('saved_foods').document(food_id)
                
                # datetime을 ISO 형식으로 변환
                saved_food_data_copy = saved_food_data.copy()
                saved_food_data_copy['savedAt'] = saved_food_data_copy['savedAt'].isoformat()
                
                saved_food_ref.set(saved_food_data_copy)
                print(f"   저장된 음식 생성: {user_uid} -> {food_id}")
        
        print("더미 데이터 생성 완료!")
        print("\n=== 생성된 데이터 구조 ===")
        print("1. users 컬렉션: 사용자 프로필 정보")
        print("2. users/{uid}/saved_foods 서브컬렉션: 각 사용자별 저장된 음식")
        print("3. countries 컬렉션: 국가 정보 (setup_firestore.py에서 생성)")
        print("4. allergy_codes 컬렉션: 알레르기 코드 (setup_firestore.py에서 생성)")
        print("5. dietary_codes 컬렉션: 식단 제한 코드 (setup_firestore.py에서 생성)")
        print("6. country_rankings 컬렉션: 국가별 음식 랭킹 (setup_firestore.py에서 생성)")
        
    except Exception as e:
        print(f"더미 데이터 생성 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    seed_dummy_data()
