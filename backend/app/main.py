from dotenv import load_dotenv
load_dotenv() #위에 있어야 오류x

from fastapi import FastAPI
from .routers import home, users, foods, auth, ai

app = FastAPI()

# 라우터 등록
app.include_router(auth.router)
app.include_router(home.router)
app.include_router(users.router)
app.include_router(ai.router) 

@app.get("/", tags=["루트"])
async def root():
    """
    ## Food Analyzer MVP API (현재 구현 상태)
    
    ### 핵심 기능:
    - **인증**: `/api/auth/me` - 토큰 검증 + 유저 upsert
    - **홈화면**: `/api/home` - 사용자 요약 + 현재 국가 Top3
    - **AI 음식 분석**: `/api/food/analyze` - 이미지 기반 AI 음식 분석
    - **OCR + 번역**: `/api/food/ocr-translate` - 메뉴판 이미지 OCR 및 번역
    - **사용자**: `/api/users/me` - 프로필 조회/수정
    - **저장 관리**: `/api/users/me/saved-foods` - 저장 목록/생성/삭제
    
    ### 시작하기:
    1. `/docs`에서 API 문서 확인
    2. `/api/auth/me`으로 Firebase ID Token으로 인증
    3. `/api/food/ocr-translate`으로 메뉴판 이미지 번역
    4. `/api/food/analyze`로 AI 음식 분석
    5. `/api/users/me/saved-foods`로 음식 저장 및 관리
    """
    return {
        "endpoints": {
            "인증": "/api/auth/me",
            "홈화면": "/api/home",
            "AI 음식 분석": "/api/food/analyze",
            "OCR + 번역": "/api/food/ocr-translate",
            "사용자": "/api/users/me",
            "저장 관리": "/api/users/me/saved-foods"
        }
    }