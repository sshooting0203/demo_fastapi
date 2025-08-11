from datetime import datetime
from dotenv import load_dotenv
import os

# .env 파일 로드 (루트 디렉토리의 .env 파일)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))

from .firestore_client import firestore_client

# Firestore 클라이언트 가져오기
db = firestore_client.db

'''
나의 생각 : 조회용 및 참고용 데이터 (SQL처럼 join을 쓸 수 없을 듯해 참고용 컬렉션 작성)
-> 개발 속도 올리려고 일단 거의 다 firestore에 올림 -> 나중에 시간 남으면 서버 캐시 이런 식으로 갈 듯
---------> 여기 데이터들은 수정X 데이터들(국가 등 추가만 할 듯)

각 컬렉션 설명 -> 0810 foodInfo와 이름 맞춤 -> 보기 쉬우라고 ...
country = 국가 선택 및 번역 시 국가-언어 매핑에 사용될 듯(이건 더 자세히 가면 iso 국가 코드 참고할 예정, 시간만 있다면..)
allergy_codes = 알레르기 이름(코드), 설명, 사실 카테고리는 나중에 쓸 것 같아서 넣었는데 지금 당장 여기선 없어도 되긴 함
dietary_codes = 종교/식단 제한 이름(코드), 간단 설명용, 먹으면 안되는 음식(알러지코드)사용
country_rankings = 각 국가별 상위 음식 순위 (검색 횟수 기준)
'''

# 국가 데이터 -> 나중에 서비스에서 지원하는 언어와 동일하게 수정
country = {
    "JP": { "code": "JP", "name": "Japan", "nameKo": "일본", "flag": "🇯🇵", "languages": ["ja", "en"] },
    "KR": { "code": "KR", "name": "South Korea", "nameKo": "한국", "flag": "🇰🇷", "languages": ["ko", "en"] },
    "US": { "code": "US", "name": "United States", "nameKo": "미국", "flag": "🇺🇸", "languages": ["en"] },
    "CN": { "code": "CN", "name": "China", "nameKo": "중국", "flag": "🇨🇳", "languages": ["zh", "en"] },
    "TH": { "code": "TH", "name": "Thailand", "nameKo": "태국", "flag": "🇹🇭", "languages": ["th", "en"] },
    "VN": { "code": "VN", "name": "Vietnam", "nameKo": "베트남", "flag": "🇻🇳", "languages": ["vi", "en"] },
    "ES": { "code": "ES", "name": "Spain", "nameKo": "스페인", "flag": "🇪🇸", "languages": ["es", "en"] },
    "IT": { "code": "IT", "name": "Italy", "nameKo": "이탈리아", "flag": "🇮🇹", "languages": ["it", "en"] },
    "FR": { "code": "FR", "name": "France", "nameKo": "프랑스", "flag": "🇫🇷", "languages": ["fr", "en"] },
    "MX": { "code": "MX", "name": "Mexico", "nameKo": "멕시코", "flag": "🇲🇽", "languages": ["es", "en"] }
}

# 알레르기 코드 데이터
allergens = {
    "EGG": {
        "code": "EGG",
        "label": "난류(가금류)",
        "icon": "🥚",
        "description": "계란, 오리알 등",
        "category": "animal"
    },
    "BEEF": {
        "code": "BEEF", 
        "label": "소고기",
        "icon": "🥩",
        "description": "소고기 및 소고기 가공품",
        "category": "meat"
    },
    "PORK": {
        "code": "PORK",
        "label": "돼지고기", 
        "icon": "🍖",
        "description": "돼지고기 및 돼지고기 가공품",
        "category": "meat"
    },
    "CHICKEN": {
        "code": "CHICKEN",
        "label": "닭고기",
        "icon": "🍗", 
        "description": "닭고기 및 닭고기 가공품",
        "category": "meat"
    },
    "SHRIMP": {
        "code": "SHRIMP",
        "label": "새우",
        "icon": "🍤",
        "description": "새우 및 새우 가공품", 
        "category": "seafood"
    },
    "CRAB": {
        "code": "CRAB",
        "label": "게",
        "icon": "🦀",
        "description": "게 및 게 가공품",
        "category": "seafood"
    },
    "SQUID": {
        "code": "SQUID", 
        "label": "오징어",
        "icon": "🦑",
        "description": "오징어 및 오징어 가공품",
        "category": "seafood"
    },
    "MACKEREL": {
        "code": "MACKEREL",
        "label": "고등어", 
        "icon": "🐟",
        "description": "고등어 및 고등어 가공품",
        "category": "seafood"
    },
    "SHELLFISH": {
        "code": "SHELLFISH",
        "label": "조개류",
        "icon": "🦪", 
        "description": "굴, 전복, 홍합 등 조개류",
        "category": "seafood"
    },
    "MILK": {
        "code": "MILK",
        "label": "우유",
        "icon": "🥛",
        "description": "우유 및 유제품",
        "category": "dairy"
    },
    "PEANUT": {
        "code": "PEANUT",
        "label": "땅콩",
        "icon": "🥜",
        "description": "땅콩 및 땅콩 가공품",
        "category": "nuts"
    },
    "WALNUT": {
        "code": "WALNUT",
        "label": "호두",
        "icon": "🌰",
        "description": "호두 및 호두 가공품",
        "category": "nuts"
    },
    "PINE_NUT": {
        "code": "PINE_NUT",
        "label": "잣",
        "icon": "🫘",
        "description": "잣 및 잣 가공품",
        "category": "nuts"
    },
    "SOY": {
        "code": "SOY",
        "label": "대두",
        "icon": "🫛",
        "description": "대두 및 대두 가공품",
        "category": "legumes"
    },
    "PEACH": {
        "code": "PEACH",
        "label": "복숭아",
        "icon": "🍑",
        "description": "복숭아 및 복숭아 가공품",
        "category": "fruits"
    },
    "TOMATO": {
        "code": "TOMATO",
        "label": "토마토",
        "icon": "🍅",
        "description": "토마토 및 토마토 가공품",
        "category": "vegetables"
    },
    "WHEAT": {
        "code": "WHEAT",
        "label": "밀",
        "icon": "🌾",
        "description": "밀 및 밀 가공품",
        "category": "grains"
    },
    "BUCKWHEAT": {
        "code": "BUCKWHEAT",
        "label": "메밀",
        "icon": "🥠",
        "description": "메밀 및 메밀 가공품",
        "category": "grains"
    },
    "SULFITES": {
        "code": "SULFITES",
        "label": "이황산류",
        "icon": "🍷",
        "description": "와인, 건과류 등에 포함된 보존료",
        "category": "preservatives"
    }
}

# 식단 제한 코드 데이터
dietaryRestrictions = {
    "HINDUISM": {
        "code": "HINDUISM",
        "label": "힌두교",
        "icon": "🕉️",
        "description": "소고기 금지",
        "restrictedFoods": ["BEEF"]
    },
    "ISLAM": {
        "code": "ISLAM",
        "label": "이슬람교", 
        "icon": "☪️",
        "description": "돼지고기 금지",
        "restrictedFoods": ["PORK"]
    },
    "VEGAN": {
        "code": "VEGAN",
        "label": "비건",
        "icon": "🌱",
        "description": "모든 동물성 식품 금지",
        "restrictedFoods": ["EGG", "BEEF", "PORK", "CHICKEN", "SHRIMP", "CRAB", "SQUID", "MACKEREL", "SHELLFISH", "MILK"]
    },
    "VEGETARIAN": {
        "code": "VEGETARIAN",
        "label": "베지테리언",
        "icon": "🥬",
        "description": "육류 금지",
        "restrictedFoods": ["BEEF", "PORK", "CHICKEN"]
    }
}

# 국가별 상위 음식 순위 데이터 (검색 횟수 기준) - 삭제됨
# countryFoodRanking = { ... } - 전체 데이터 삭제


# 더미 사용자 데이터 제거 - seed_dummy_firestore.py에서 처리

def setup_firestore():
    """Firestore 초기 설정 (참조용 데이터만)"""
    print("Firestore 초기 설정 시작")
    
    # 1. 국가 데이터 생성
    print("1. 국가 데이터 생성 중")
    for country_code, data in country.items():
        db.collection('country').document(country_code).set(data)
        print(f"   - {country_code}: {data['nameKo']} 생성 완료")
    
    # 2. 알레르기 코드 데이터 생성
    print("2. 알레르기 코드 데이터 생성 중")
    for allergy_code, data in allergens.items():
        db.collection('allergens').document(allergy_code).set(data)
        print(f"   - {allergy_code}: {data['label']} 생성 완료")
    
    # 3. 식단 제한 코드 데이터 생성
    print("3. 식단 제한 코드 데이터 생성 중")
    for dietary_code, data in dietaryRestrictions.items():
        db.collection('dietaryRestrictions').document(dietary_code).set(data)
        print(f"   - {dietary_code}: {data['label']} 생성 완료")

    print("Firestore 초기 설정 완료 (참조용 데이터)")

if __name__ == "__main__":
    setup_firestore()
