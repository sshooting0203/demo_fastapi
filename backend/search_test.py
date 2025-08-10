# tests/test_search_food.py
import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from app.services.user_service import get_current_user
from app.routers import home, users, search, auth, ai
import app.services.search_service as search_module 
from app.routers import search

@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(auth.router)
    app.include_router(home.router)
    app.include_router(users.router)
    app.include_router(search.router)
    app.include_router(ai.router) 
    return app

@pytest.mark.anyio
async def test_search_food_authed_success(monkeypatch, app):
    # 1) get_current_user 의존성 오버라이드 (uid 존재)
    async def mock_dep():
        return {"uid": "user_001", "email": "test1@example.com"}
    
    app.dependency_overrides[search.get_current_user] = mock_dep
    
    # 2) 서비스 모킹
    # 응답 모델에 맞는 최소 dict (필드는 프로젝트 모델에 맞게 조정)
    async def mock_search_food(request, uid):
        return {
            "foodId": "JP_Abc",
            "foodInfo": {
                "foodName": request.food_name,
                "dishName": request.food_name,
                "country": request.country or "JP",
                "summary": "요약",
                "recommendations": ["추천1"],
                "ingredients": ["재료1"],
                "allergens": ["MILK"],
                "imageUrl": "https://example.com/img.jpg",
                "imageSource": "Crawling",
                "culturalBackground": "배경",
            },
            "isSaved": False,
            "searchCount": 0,
        }
    calls = {"log": [], "rank": []}

    async def mock_log_search(uid, query, country):
        calls["log"].append((uid, query, country))

    async def mock_update_country_ranking(country, query):
        calls["rank"].append((country, query))

    monkeypatch.setattr(search.search_service, "search_food", mock_search_food, raising=False)
    monkeypatch.setattr(search.search_service, "log_search", mock_log_search, raising=False)
    monkeypatch.setattr(search.ranking_service, "update_country_ranking", mock_update_country_ranking, raising=False)

    payload = {
        "source_language": "ja",
        "target_language": "ko",
        "country": "JP",
        "food_name": "Chistorra",
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/search/", json=payload)

    assert res.status_code == 200
    body = res.json()
    assert body["foodId"].startswith("JP_")
    assert body["foodInfo"]["foodName"] == "Chistorra"
    assert calls["log"] == [("user_001", "Chistorra", "JP")]
    assert calls["rank"] == [("JP", "Chistorra")]

@pytest.mark.anyio
async def test_search_food_unauthed(monkeypatch, app):
    # 로그인 안 된 경우: get_current_user → None
    async def mock_dep():
        return None
    app.dependency_overrides[search.get_current_user] = mock_dep 
    # app.dependency_overrides[search.get_current_user] = lambda: None

    async def mock_search_food(request, uid):
        return {
            "foodId": "JP_Abc",
            "foodInfo": {
                "foodName": request.food_name,
                "dishName": request.food_name,
                "country": request.country or "JP",
                "summary": "요약",
                "recommendations": ["추천1"],
                "ingredients": ["재료1"],
                "allergens": ["MILK"],
                "imageUrl": "https://example.com/img.jpg",
                "imageSource": "Crawling",
                "culturalBackground": "배경",
            },
            "isSaved": False,
            "searchCount": 0,
        }

    logged = {"log": [], "rank": []}
    async def mock_log_search(uid, query, country):
        logged["log"].append(1)
    async def mock_update_country_ranking(country, query):
        logged["rank"].append((country, query))

    monkeypatch.setattr(search.search_service, "search_food", mock_search_food, raising=False)
    monkeypatch.setattr(search.search_service, "log_search", mock_log_search, raising=False)
    monkeypatch.setattr(search.ranking_service, "update_country_ranking", mock_update_country_ranking, raising=False)

    payload = {
        "source_language": "ja",
        "target_language": "ko",
        "country": "JP",
        "food_name": "Ramen",
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/search/", json=payload)

    assert res.status_code == 200
    # uid가 없으니 log_search는 호출되지 않아야 함
    assert logged["log"] == []
    # country는 있으니 랭킹은 업데이트
    assert logged["rank"] == [("JP", "Ramen")]

@pytest.mark.anyio
async def test_search_food_validation_error(app):

    app.dependency_overrides[search.get_current_user] = lambda: None
    # 필수 필드 누락 → 422
    bad_payload = {
        "source_language": "ja",
        "target_language": "ko",
        # "food_name" 누락
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/search/", json=bad_payload)
    assert res.status_code == 422
