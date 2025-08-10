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
        
        # FoodInfo 모델 구조에 맞는 음식 데이터
        food_info_data = [
            {
                "foodId": "JP_tonkatsu",
                "foodInfo": {
                    "foodName": "돈카츠",
                    "dishName": "とんかつ",
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
                    "dishName": "ラーメン",
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
                "foodId": "KR_bibimbap",
                "foodInfo": {
                    "foodName": "비빔밥",
                    "dishName": "비빔밥",
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
                    "dishName": "떡볶이",
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
                "foodId": "US_burger",
                "foodInfo": {
                    "foodName": "치즈버거",
                    "dishName": "Cheeseburger",
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
                    "dishName": "Pizza",
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
                "foodId": "CN_kungpao",
                "foodInfo": {
                    "foodName": "궁보계정",
                    "dishName": "宫保鸡丁",
                    "country": "CN",
                    "summary": "닭고기와 땅콩을 매콤달콤하게 볶은 사천 요리입니다.",
                    "recommendations": ["중식 애호가", "매콤달콤한 맛 선호"],
                    "ingredients": ["닭고기", "땅콩", "말린 고추", "간장"],
                    "allergens": ["CHICKEN", "PEANUT", "SOY"],
                    "imageUrl": "https://picsum.photos/seed/food_CN_kungpao/800/500",
                    "imageSource": "중국 사천요리 사진",
                    "culturalBackground": "칭 왕조 관리였던 궁보의 이름에서 유래했다는 설이 있습니다."
                }
            },
            {
                "foodId": "CN_xiaolongbao",
                "foodInfo": {
                    "foodName": "샤오롱바오",
                    "dishName": "小笼包",
                    "country": "CN",
                    "summary": "얇은 피에 육즙 가득한 속을 넣어 찐 딤섬입니다.",
                    "recommendations": ["딤섬 애호가", "국물 만두 선호"],
                    "ingredients": ["밀가루 피", "돼지고기 속", "육수 젤리"],
                    "allergens": ["WHEAT", "PORK"],
                    "imageUrl": "https://picsum.photos/seed/food_CN_xiaolongbao/800/500",
                    "imageSource": "상하이 딤섬 사진",
                    "culturalBackground": "상하이 지역에서 특히 유명한 대표 딤섬입니다."
                }
            },
            {
                "foodId": "TH_padthai",
                "foodInfo": {
                    "foodName": "팟타이",
                    "dishName": "ผัดไทย",
                    "country": "TH",
                    "summary": "볶음쌀국수에 새우, 두부, 숙주 등을 넣어 만든 태국 요리입니다.",
                    "recommendations": ["면 요리 선호자", "아시아 음식 애호가"],
                    "ingredients": ["쌀국수", "새우", "두부", "숙주", "땅콩"],
                    "allergens": ["PEANUT", "SOY", "SHRIMP"],
                    "imageUrl": "https://picsum.photos/seed/food_TH_padthai/800/500",
                    "imageSource": "태국 길거리 음식 사진",
                    "culturalBackground": "국가 주도의 식문화 캠페인으로 대중화되었다고 알려져 있습니다."
                }
            },
            {
                "foodId": "VN_pho",
                "foodInfo": {
                    "foodName": "퍼(쌀국수)",
                    "dishName": "Phở",
                    "country": "VN",
                    "summary": "향신료가 들어간 맑은 육수와 쌀국수가 특징인 베트남 국수입니다.",
                    "recommendations": ["가벼운 국물 선호", "아침 식사"],
                    "ingredients": ["쌀국수", "소고기/닭고기 육수", "허브", "라임"],
                    "allergens": ["BEEF"],
                    "imageUrl": "https://picsum.photos/seed/food_VN_pho/800/500",
                    "imageSource": "하노이 길거리 식당 사진",
                    "culturalBackground": "북부와 남부 스타일이 다르게 발전했습니다."
                }
            },
            {
                "foodId": "ES_paella",
                "foodInfo": {
                    "foodName": "파에야",
                    "dishName": "Paella",
                    "country": "ES",
                    "summary": "사프란 향이 나는 쌀요리에 해산물 또는 고기를 넣어 지은 스페인 요리입니다.",
                    "recommendations": ["해산물 애호가", "파티용 대접 요리"],
                    "ingredients": ["쌀", "사프란", "해산물", "올리브 오일"],
                    "allergens": ["SHELLFISH", "SHRIMP"],
                    "imageUrl": "https://picsum.photos/seed/food_ES_paella/800/500",
                    "imageSource": "발렌시아 전통 요리 사진",
                    "culturalBackground": "발렌시아 지방에서 시작된 축제 음식입니다."
                }
            },
            {
                "foodId": "IT_carbonara",
                "foodInfo": {
                    "foodName": "카르보나라",
                    "dishName": "Carbonara",
                    "country": "IT",
                    "summary": "계란과 치즈, 판체타로 만드는 로마식 파스타입니다.",
                    "recommendations": ["크리미 파스타 선호", "이탈리아 음식 애호가"],
                    "ingredients": ["파스타", "계란", "치즈", "판체타", "후추"],
                    "allergens": ["WHEAT", "EGG", "MILK", "PORK"],
                    "imageUrl": "https://picsum.photos/seed/food_IT_carbonara/800/500",
                    "imageSource": "로마 가정식 사진",
                    "culturalBackground": "전통적으로 생크림 없이 계란과 치즈로만 만듭니다."
                }
            },
            {
                "foodId": "FR_crepe",
                "foodInfo": {
                    "foodName": "크레페",
                    "dishName": "Crêpe",
                    "country": "FR",
                    "summary": "얇게 부친 프랑스식 팬케이크로 달콤·짭짤 토핑 모두 어울립니다.",
                    "recommendations": ["디저트 애호가", "브런치 선호"],
                    "ingredients": ["밀가루", "우유", "계란", "버터"],
                    "allergens": ["WHEAT", "MILK", "EGG"],
                    "imageUrl": "https://picsum.photos/seed/food_FR_crepe/800/500",
                    "imageSource": "파리 카페 사진",
                    "culturalBackground": "브르타뉴 지역의 갈레트와 함께 유명합니다."
                }
            },
            {
                "foodId": "MX_tacosalpastor",
                "foodInfo": {
                    "foodName": "타코 알 파스토르",
                    "dishName": "Tacos al Pastor",
                    "country": "MX",
                    "summary": "아도보로 양념한 돼지고기를 회전구이해 얇게 썰어 넣는 멕시코 타코입니다.",
                    "recommendations": ["길거리 음식 애호가", "매콤한 맛 선호"],
                    "ingredients": ["옥수수 또르띠야", "돼지고기", "파인애플", "양파", "고추"],
                    "allergens": ["PORK"],
                    "imageUrl": "https://picsum.photos/seed/food_MX_alpastor/800/500",
                    "imageSource": "멕시코 시티 길거리 사진",
                    "culturalBackground": "레바논계 이민자들의 샤와르마 문화가 멕시코에서 변형된 요리입니다."
                }
            }
        ]
        
        # ==================== 사용자별 저장된 음식 데이터 생성 ====================
        print("3. 사용자별 저장된 음식 데이터 생성 중...")
        
        # 각 사용자별로 4개씩, 국가 섞어서 저장
        user_foods_mapping = {
            "user_001": ["JP_tonkatsu", "KR_bibimbap", "US_burger", "TH_padthai"],
            "user_002": ["KR_tteokbokki", "JP_ramen", "CN_kungpao", "ES_paella"],
            "user_003": ["US_pizza", "FR_crepe", "VN_pho", "MX_tacosalpastor"]
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
                saved_food_ref = db.collection('users').document(user_uid).collection('saveFoods').document(food_id)
                
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
