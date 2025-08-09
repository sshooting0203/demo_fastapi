import os
import json
from datetime import datetime, timezone
from typing import Dict, List

from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

"""
기능 테스트용 : '더미 데이터'만 주입
- 기존 참조 컬렉션(countries, allergy_codes, dietary_codes)과는 별도임. 얜 삭제하고 수정할 거.
- 더미 전용 ID에 'DUMMY_' 접두사를 사용해서 구분할 거 ...
"""

DEMO_UID = "DUMMY_user_01"
DEMO_EMAIL = "dummy1@example.com"
DEFAULT_CURRENT_COUNTRY = "ES"  # 홈 화면 테스트용 -> 나라 입력 시 NULL 아니게 됨(POST 형식으로 처리할 듯?)

# 국가별 더미 랭킹 원장(foods) + popular_foods 더미
POPULAR_FOODS_SEED: List[Dict] = [
    {
        "id": "DUMMY_JP_tonkatsu",
        "country": "JP",
        "slug": "tonkatsu",
        "names": {"default": "Tonkatsu", "ko": "돈카츠", "ja": "とんかつ"},
        "foodInfo": {
            "summary": "바삭한 빵가루 튀김을 입힌 일본식 돼지고기 커틀릿.",
            "ingredients": ["pork", "breadcrumbs", "egg", "flour", "cabbage", "sauce"],
            "allergens": ["EGG","WHEAT"],
            "imageUrl": "https://example.com/tonkatsu.jpg",
            "imageSource": "seed",
            "culturalBackground": "요쇼쿠 계열 서양식의 일본 현지화 메뉴."
        },
        "searchCount": 123,
        "saveCount": 45,
    },
    {
        "id": "DUMMY_ES_paella",
        "country": "ES",
        "slug": "paella",
        "names": {"default": "Paella", "ko": "빠에야", "es": "Paella"},
        "foodInfo": {
            "summary": "사프란 향의 쌀과 해산물/고기를 함께 끓여낸 스페인 대표 요리.",
            "ingredients": ["rice", "saffron", "seafood", "chicken", "peas"],
            "allergens": ["SHELLFISH"],
            "imageUrl": "https://example.com/paella.jpg",
            "imageSource": "seed",
            "culturalBackground": "발렌시아 지역에서 유래한 전통 요리."
        },
        "searchCount": 98,
        "saveCount": 51,
    },
    {
        "id": "DUMMY_FR_crepe",
        "country": "FR",
        "slug": "crepe",
        "names": {"default": "Crêpe", "ko": "크레페", "fr": "Crêpe"},
        "foodInfo": {
            "summary": "얇게 부친 프랑스식 팬케이크로 달콤/짭짤 토핑과 곁들여 먹는다.",
            "ingredients": ["wheat flour", "egg", "milk", "butter"],
            "allergens": ["WHEAT","EGG","MILK"],
            "imageUrl": "https://example.com/crepe.jpg",
            "imageSource": "seed",
            "culturalBackground": "브르타뉴 지역이 유명하며 길거리 간식으로도 대중적."
        },
        "searchCount": 76,
        "saveCount": 22,
    },
]

# 데모 유저가 저장한 음식
SAVED_FOODS_FOR_DEMO: List[Dict] = [
    {
        "id": "DUMMY_JP_tonkatsu",
        "country": "JP",
        "foodName": "Tonkatsu",
        "translatedText": "돈카츠",
        "userImageUrl": "https://example.com/user_tonkatsu.jpg",
        "summaryShort": "바삭한 일본식 커틀릿",
        "allergens": ["EGG","WHEAT"],
        "restaurantName": "Maisen Aoyama",
        "review": "정말 바삭했고 소스가 좋았음",
        "rating": 4.5,
    },
    {
        "id": "DUMMY_ES_paella",
        "country": "ES",
        "foodName": "Paella",
        "translatedText": "빠에야",
        "userImageUrl": "https://example.com/user_paella.jpg",
        "summaryShort": "사프란 향의 해산물 쌀요리",
        "allergens": ["SHELLFISH"],
        "restaurantName": "Bar La Pepa",
        "review": "향이 진하고 해산물이 신선",
        "rating": 4.0,
    },
]

# 검색 로그(TTL 대상)
SEARCH_LOGS_SEED: List[Dict] = [
    {
        "id": "DUMMY_log_1",
        "userId": DEMO_UID,
        "country": "JP",
        "foodId": "DUMMY_JP_tonkatsu",
        "originalText": "とんかつ",
        "translatedText": "돈카츠",
        "searchType": "text",
        "retentionDays": 30,
    },
    {
        "id": "DUMMY_log_2",
        "userId": DEMO_UID,
        "country": "ES",
        "foodId": "DUMMY_ES_paella",
        "originalText": "Paella",
        "translatedText": "빠에야",
        "searchType": "text",
        "retentionDays": 30,
    },
    {
        "id": "DUMMY_log_3",
        "userId": DEMO_UID,
        "country": "FR",
        "foodId": "DUMMY_FR_crepe",
        "originalText": "Crêpe",
        "translatedText": "크레페",
        "searchType": "ocr",
        "retentionDays": 30,
    },
]

# -----------------------------
# Firestore 초기화
# -----------------------------
load_dotenv()
firebase_credentials = json.loads(os.getenv("FIREBASE_CREDENTIALS"))
cred = credentials.Certificate(firebase_credentials)
firebase_admin.initialize_app(cred)
db = firestore.client()

def now_utc():
    return datetime.now(timezone.utc)

def upsert(col: str, doc_id: str, data: dict):
    db.collection(col).document(doc_id).set(data, merge=True)

def upsert_sub(parent_ref, subcol: str, doc_id: str, data: dict):
    parent_ref.collection(subcol).document(doc_id).set(data, merge=True)

def seed_user_and_saved():
    print("▶ Seeding demo user & saved_foods ...")
    user_ref = db.collection("users").document(DEMO_UID)
    upsert("users", DEMO_UID, {
        "uid": DEMO_UID,
        "email": DEMO_EMAIL,
        "allergies": ["EGG"],
        "dietaryRestrictions": ["VEGETARIAN"],  # 배열 형태긴 함
        "currentCountry": DEFAULT_CURRENT_COUNTRY,
        "createdAt": now_utc(),
        "updatedAt": now_utc(),
    })
    # saved_foods
    for item in SAVED_FOODS_FOR_DEMO:
        upsert_sub(user_ref, "saved_foods", item["id"], {
            **item,
            "savedAt": now_utc(),
        })
        print(f"  - users/{DEMO_UID}/saved_foods/{item['id']} upserted")

def seed_popular_foods():
    print("▶ Seeding popular_foods ...")
    for f in POPULAR_FOODS_SEED:
        upsert("popular_foods", f["id"], {
            "id": f["id"],
            "country": f["country"],
            "slug": f["slug"],
            "names": f["names"],
            "foodInfo": f["foodInfo"],
            "searchCount": f["searchCount"],
            "saveCount": f["saveCount"],
            "lastSearched": now_utc(),
            "createdAt": now_utc(),
            "updatedAt": now_utc(),
        })
        print(f"  - popular_foods/{f['id']} upserted")

def seed_country_rankings():
    print("▶ Seeding country_rankings (foods ledger + top snapshot) ...")

    # 국가별로 묶기
    by_country: Dict[str, List[Dict]] = {}
    for f in POPULAR_FOODS_SEED:
        by_country.setdefault(f["country"], []).append(f)

    for country, items in by_country.items():
        country_ref = db.collection("country_rankings").document(country)

        # 1) 루트 문서 생성(있으면 병합)
        country_ref.set({"lastTopSnapshotAt": now_utc()}, merge=True)

        # 2) foods 원장(서브컬렉션)
        for f in items:
            ledger_doc = {
                "foodId": f["id"],
                "searchCount": f["searchCount"],
                "saveCount": f["saveCount"],
                "lastSearched": now_utc(),
                "lastSaved": now_utc(),
            }
            country_ref.collection("foods").document(f["id"]).set(ledger_doc, merge=True)
            print(f"  - country_rankings/{country}/foods/{f['id']} upserted")

        # 3) Top3 스냅샷(루트 문서 필드)
        top3 = sorted(items, key=lambda x: (-x["searchCount"], -x["saveCount"]))[:3]
        top_payload = {
            "topFoods": [
                {
                    "foodId": f["id"],
                    "foodName": f["names"].get("default", ""),
                    "imageUrl": f["foodInfo"].get("imageUrl", ""),
                    "searchCount": f.get("searchCount", 0),
                    "saveCount": f.get("saveCount", 0),
                } for f in top3
            ],
            "snapshotAt": now_utc()
        }
        country_ref.set(top_payload, merge=True)  # ← 문서 필드로 저장한다고 해야 함 어렵군
        print(f"  - country_rankings/{country} top snapshot updated")

def seed_search_logs():
    print("▶ Seeding search_logs (TTL 대상) ...")
    for log in SEARCH_LOGS_SEED:
        upsert("search_logs", log["id"], {
            **log,
            "timestamp": now_utc(),
        })
        print(f"  - search_logs/{log['id']} upserted")

def main():
    print("== Firestore dummy seed start ==")
    seed_user_and_saved()
    seed_popular_foods()
    seed_country_rankings()
    seed_search_logs()
    print("== Firestore dummy seed done ==")

if __name__ == "__main__":
    main()