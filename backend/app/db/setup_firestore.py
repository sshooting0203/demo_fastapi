from datetime import datetime
from .firestore_client import firestore_client

# Firestore 클라이언트 가져오기
db = firestore_client.db

'''
나의 생각 : 조회용 및 참고용 데이터 (SQL처럼 join을 쓸 수 없을 듯해 참고용 컬렉션 작성)
-> 개발 속도 올리려고 일단 거의 다 firestore에 올림 -> 나중에 시간 남으면 서버 TTL 캐시 이런 식으로 갈 듯
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

# 국가별 상위 음식 순위 데이터 (검색 횟수 기준)
countryFoodRanking = {
    "JP": {
        "countryCode": "JP",
        "countryName": "일본",
        "topFoods": [
        { "foodId": "JP_sushi", "foodName": "초밥", "searchCount": 320, "saveCount": 210 },
        { "foodId": "JP_ramen", "foodName": "라멘", "searchCount": 295, "saveCount": 185 },
        { "foodId": "JP_tonkatsu", "foodName": "돈카츠", "searchCount": 248, "saveCount": 156 },
        { "foodId": "JP_tempura", "foodName": "덴푸라", "searchCount": 231, "saveCount": 143 },
        { "foodId": "JP_udon", "foodName": "우동", "searchCount": 214, "saveCount": 128 },
        { "foodId": "JP_gyoza", "foodName": "교자", "searchCount": 198, "saveCount": 119 },
        { "foodId": "JP_okonomiyaki", "foodName": "오코노미야키", "searchCount": 184, "saveCount": 108 },
        { "foodId": "JP_yakitori", "foodName": "야키토리", "searchCount": 169, "saveCount": 97 },
        { "foodId": "JP_curry", "foodName": "일본식 카레", "searchCount": 156, "saveCount": 88 },
        { "foodId": "JP_soba", "foodName": "소바", "searchCount": 141, "saveCount": 79 }
        ]
    },
    "KR": {
        "countryCode": "KR",
        "countryName": "한국",
        "topFoods": [
        { "foodId": "KR_bibimbap", "foodName": "비빔밥", "searchCount": 260, "saveCount": 164 },
        { "foodId": "KR_bulgogi", "foodName": "불고기", "searchCount": 244, "saveCount": 152 },
        { "foodId": "KR_kimchi", "foodName": "김치", "searchCount": 228, "saveCount": 138 },
        { "foodId": "KR_japchae", "foodName": "잡채", "searchCount": 212, "saveCount": 126 },
        { "foodId": "KR_samgyeopsal", "foodName": "삼겹살", "searchCount": 196, "saveCount": 115 },
        { "foodId": "KR_tteokbokki", "foodName": "떡볶이", "searchCount": 183, "saveCount": 105 },
        { "foodId": "KR_kimchijjigae", "foodName": "김치찌개", "searchCount": 171, "saveCount": 96 },
        { "foodId": "KR_naengmyeon", "foodName": "비빔냉면", "searchCount": 159, "saveCount": 88 },
        { "foodId": "KR_sundubu", "foodName": "순두부찌개", "searchCount": 147, "saveCount": 80 },
        { "foodId": "KR_galbi", "foodName": "갈비", "searchCount": 135, "saveCount": 72 }
        ]
    },
    "US": {
        "countryCode": "US",
        "countryName": "미국",
        "topFoods": [
        { "foodId": "US_burger", "foodName": "햄버거", "searchCount": 305, "saveCount": 204 },
        { "foodId": "US_pizza", "foodName": "피자", "searchCount": 287, "saveCount": 190 },
        { "foodId": "US_hotdog", "foodName": "핫도그", "searchCount": 229, "saveCount": 140 },
        { "foodId": "US_steak", "foodName": "스테이크", "searchCount": 251, "saveCount": 162 },
        { "foodId": "US_friedchicken", "foodName": "프라이드치킨", "searchCount": 238, "saveCount": 151 },
        { "foodId": "US_macncheese", "foodName": "맥앤치즈", "searchCount": 201, "saveCount": 120 },
        { "foodId": "US_bbqribs", "foodName": "바비큐 립", "searchCount": 188, "saveCount": 112 },
        { "foodId": "US_pancakes", "foodName": "팬케이크", "searchCount": 177, "saveCount": 104 },
        { "foodId": "US_caesarsalad", "foodName": "시저샐러드", "searchCount": 162, "saveCount": 93 },
        { "foodId": "US_clamchowder", "foodName": "클램차우더", "searchCount": 148, "saveCount": 85 }
        ]
    },
    "CN": {
        "countryCode": "CN",
        "countryName": "중국",
        "topFoods": [
        { "foodId": "CN_dimsum", "foodName": "딤섬", "searchCount": 270, "saveCount": 158 },
        { "foodId": "CN_kungpao", "foodName": "궁보계정", "searchCount": 256, "saveCount": 149 },
        { "foodId": "CN_mapo", "foodName": "마파두부", "searchCount": 231, "saveCount": 136 },
        { "foodId": "CN_xiaolongbao", "foodName": "샤오롱바오", "searchCount": 218, "saveCount": 128 },
        { "foodId": "CN_pekingduck", "foodName": "북경오리", "searchCount": 205, "saveCount": 121 },
        { "foodId": "CN_friedrice", "foodName": "볶음밥", "searchCount": 192, "saveCount": 112 },
        { "foodId": "CN_chowmein", "foodName": "차오메인", "searchCount": 179, "saveCount": 104 },
        { "foodId": "CN_wontonsoup", "foodName": "완탕수프", "searchCount": 167, "saveCount": 96 },
        { "foodId": "CN_sweetsourpork", "foodName": "탕수육", "searchCount": 155, "saveCount": 88 },
        { "foodId": "CN_maponoodles", "foodName": "탄탄면", "searchCount": 143, "saveCount": 80 }
        ]
    },
    "TH": {
        "countryCode": "TH",
        "countryName": "태국",
        "topFoods": [
        { "foodId": "TH_padthai", "foodName": "팟타이", "searchCount": 258, "saveCount": 152 },
        { "foodId": "TH_tomyum", "foodName": "똠얌", "searchCount": 236, "saveCount": 139 },
        { "foodId": "TH_greencurry", "foodName": "그린커리", "searchCount": 214, "saveCount": 127 },
        { "foodId": "TH_massaman", "foodName": "마사만커리", "searchCount": 198, "saveCount": 118 },
        { "foodId": "TH_somtam", "foodName": "솜탐", "searchCount": 183, "saveCount": 108 },
        { "foodId": "TH_larb", "foodName": "랍", "searchCount": 169, "saveCount": 99 },
        { "foodId": "TH_padkrapao", "foodName": "팟끄라파오", "searchCount": 157, "saveCount": 92 },
        { "foodId": "TH_mangostickyrice", "foodName": "망고 스티키 라이스", "searchCount": 146, "saveCount": 86 },
        { "foodId": "TH_redcurry", "foodName": "레드커리", "searchCount": 135, "saveCount": 79 },
        { "foodId": "TH_tomkhagai", "foodName": "톰카가이", "searchCount": 124, "saveCount": 72 }
        ]
    },
    "VN": {
        "countryCode": "VN",
        "countryName": "베트남",
        "topFoods": [
        { "foodId": "VN_pho", "foodName": "퍼(쌀국수)", "searchCount": 241, "saveCount": 145 },
        { "foodId": "VN_banhmi", "foodName": "반미", "searchCount": 225, "saveCount": 135 },
        { "foodId": "VN_springroll", "foodName": "스프링롤", "searchCount": 209, "saveCount": 126 },
        { "foodId": "VN_bunbo", "foodName": "분보", "searchCount": 194, "saveCount": 116 },
        { "foodId": "VN_comtam", "foodName": "껌떤", "searchCount": 180, "saveCount": 108 },
        { "foodId": "VN_buncha", "foodName": "분짜", "searchCount": 167, "saveCount": 99 },
        { "foodId": "VN_caolau", "foodName": "까오러우", "searchCount": 155, "saveCount": 92 },
        { "foodId": "VN_banhxeo", "foodName": "반세오", "searchCount": 143, "saveCount": 84 },
        { "foodId": "VN_cakhoto", "foodName": "까코또", "searchCount": 132, "saveCount": 78 },
        { "foodId": "VN_bunrieu", "foodName": "분리우", "searchCount": 121, "saveCount": 71 }
        ]
    },
    "ES": {
        "countryCode": "ES",
        "countryName": "스페인",
        "topFoods": [
        { "foodId": "ES_paella", "foodName": "파에야", "searchCount": 252, "saveCount": 160 },
        { "foodId": "ES_tortilla", "foodName": "또르티야 에스파뇰라", "searchCount": 231, "saveCount": 146 },
        { "foodId": "ES_jamon", "foodName": "하몬", "searchCount": 215, "saveCount": 134 },
        { "foodId": "ES_gazpacho", "foodName": "가스파초", "searchCount": 199, "saveCount": 123 },
        { "foodId": "ES_churros", "foodName": "추로스", "searchCount": 186, "saveCount": 114 },
        { "foodId": "ES_patatasbravas", "foodName": "파타타스 브라바스", "searchCount": 172, "saveCount": 105 },
        { "foodId": "ES_croquetas", "foodName": "크로케타", "searchCount": 159, "saveCount": 96 },
        { "foodId": "ES_fabada", "foodName": "파바다", "searchCount": 146, "saveCount": 88 },
        { "foodId": "ES_pulpo", "foodName": "문어요리(풀포)", "searchCount": 134, "saveCount": 80 },
        { "foodId": "ES_ensaladarusa", "foodName": "엔살라다 루사", "searchCount": 123, "saveCount": 74 }
        ]
    },
    "IT": {
        "countryCode": "IT",
        "countryName": "이탈리아",
        "topFoods": [
        { "foodId": "IT_pizzamargherita", "foodName": "피자 마르게리타", "searchCount": 310, "saveCount": 205 },
        { "foodId": "IT_carbonara", "foodName": "카르보나라", "searchCount": 289, "saveCount": 192 },
        { "foodId": "IT_lasagna", "foodName": "라자냐", "searchCount": 266, "saveCount": 178 },
        { "foodId": "IT_risotto", "foodName": "리소토", "searchCount": 242, "saveCount": 162 },
        { "foodId": "IT_tiramisu", "foodName": "티라미수", "searchCount": 225, "saveCount": 149 },
        { "foodId": "IT_bruschetta", "foodName": "브루스케타", "searchCount": 209, "saveCount": 138 },
        { "foodId": "IT_gnocchi", "foodName": "뇨키", "searchCount": 193, "saveCount": 127 },
        { "foodId": "IT_ossobuco", "foodName": "오소부코", "searchCount": 178, "saveCount": 118 },
        { "foodId": "IT_minestrone", "foodName": "미네스트로네", "searchCount": 164, "saveCount": 108 },
        { "foodId": "IT_trofiepesto", "foodName": "트로피에 알 페스토", "searchCount": 151, "saveCount": 99 }
        ]
    },
    "FR": {
        "countryCode": "FR",
        "countryName": "프랑스",
        "topFoods": [
        { "foodId": "FR_coqauvin", "foodName": "꼬코뱅", "searchCount": 238, "saveCount": 150 },
        { "foodId": "FR_ratatouille", "foodName": "라따뚜이", "searchCount": 222, "saveCount": 141 },
        { "foodId": "FR_bouillabaisse", "foodName": "부야베스", "searchCount": 207, "saveCount": 131 },
        { "foodId": "FR_quichelorraine", "foodName": "키슈 로렌", "searchCount": 194, "saveCount": 123 },
        { "foodId": "FR_steakfrites", "foodName": "스테이크 프리츠", "searchCount": 181, "saveCount": 115 },
        { "foodId": "FR_croquemonsieur", "foodName": "크로크 무슈", "searchCount": 169, "saveCount": 107 },
        { "foodId": "FR_crepe", "foodName": "크레페", "searchCount": 158, "saveCount": 100 },
        { "foodId": "FR_cassoulet", "foodName": "카슐레", "searchCount": 146, "saveCount": 92 },
        { "foodId": "FR_nicoisesalad", "foodName": "니수아즈 샐러드", "searchCount": 135, "saveCount": 85 },
        { "foodId": "FR_boeufbourguignon", "foodName": "뵈프 부르기뇽", "searchCount": 124, "saveCount": 78 }
        ]
    },
    "MX": {
        "countryCode": "MX",
        "countryName": "멕시코",
        "topFoods": [
        { "foodId": "MX_tacosalpastor", "foodName": "타코 알 파스토르", "searchCount": 246, "saveCount": 156 },
        { "foodId": "MX_enchiladas", "foodName": "엔칠라다", "searchCount": 228, "saveCount": 144 },
        { "foodId": "MX_guacamole", "foodName": "과카몰리", "searchCount": 212, "saveCount": 133 },
        { "foodId": "MX_chilaquiles", "foodName": "칠라킬레스", "searchCount": 197, "saveCount": 124 },
        { "foodId": "MX_tamales", "foodName": "타말", "searchCount": 183, "saveCount": 115 },
        { "foodId": "MX_molepoblano", "foodName": "몰레 포블라노", "searchCount": 170, "saveCount": 107 },
        { "foodId": "MX_quesadilla", "foodName": "케사디야", "searchCount": 158, "saveCount": 99 },
        { "foodId": "MX_pozole", "foodName": "포졸레", "searchCount": 146, "saveCount": 92 },
        { "foodId": "MX_elote", "foodName": "엘로테", "searchCount": 135, "saveCount": 84 },
        { "foodId": "MX_ceviche", "foodName": "세비체", "searchCount": 124, "saveCount": 78 }
        ]
    }
}


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
    
    # 4. 국가별 상위 음식 순위 데이터 생성
    print("4. 국가별 상위 음식 순위 데이터 생성 중")
    for country_code, data in countryFoodRanking.items():
        db.collection('countryFoodRanking').document(country_code).set(data)
        print(f"   - {country_code}: {data['countryName']} 상위 음식 생성 완료")

    print("Firestore 초기 설정 완료 (참조용 데이터)")

if __name__ == "__main__":
    setup_firestore()
