from dotenv import load_dotenv
load_dotenv() #위에 있어야 오류x

from fastapi import FastAPI
from .routers import home, users, search, auth

app = FastAPI()

# 라우터 등록
app.include_router(auth.router)
app.include_router(home.router)
app.include_router(users.router)
app.include_router(search.router)

@app.get("/", tags=["루트"])
async def root():
    """
    ## Food Analyzer MVP API
    
    ### 핵심 기능:
    - **인증**: `/api/auth/login` - Google OAuth 로그인 (Firebase ID Token)
    - **홈화면**: `/api/home` - 사용자 정보 + 여행국가 Top 3 음식
    - **음식 검색**: `/api/search` - OCR/번역 결과를 AI 음식 설명으로 변환
    - **사용자 관리**: `/api/users/{uid}/profile` - 프로필 조회/수정
    - **음식 저장**: `/api/users/{uid}/save-food` - AI 음식 설명 저장
    - **마이페이지**: `/api/users/{uid}/saved-foods` - 저장된 음식 목록
    - **음식 삭제**: `/api/users/{uid}/delete-foods` - 저장된 음식 일괄 삭제
    
    ### 시작하기:
    1. `/docs`에서 API 문서 확인
    2. `/api/auth/login`으로 Firebase ID Token으로 로그인
    3. 음식 사진 업로드 및 분석
    4. AI 음식 설명 저장 및 관리
    """
    return {
        "greeting": "Food Analyzer MVP API에 오신 것을 환영합니다!",
        "message": "AI 기반 음식 분석 및 저장 서비스입니다.",
        "version": "1.0.0-MVP",
        "docs": "/docs",
        "endpoints": {
            "인증": "/api/auth/login",
            "홈화면": "/api/home",
            "음식 검색": "/api/search",
            "사용자": "/api/users/{uid}/profile",
            "음식 저장": "/api/users/{uid}/save-food",
            "마이페이지": "/api/users/{uid}/saved-foods",
            "음식 삭제": "/api/users/{uid}/delete-foods"
        },
        "features": [
            "Google OAuth 로그인",
            "AI 음식 분석",
            "사용자별 음식 저장",
            "마이페이지 관리",
            "여행 국가별 음식 랭킹"
        ]
    }