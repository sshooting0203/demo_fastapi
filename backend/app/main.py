from dotenv import load_dotenv
load_dotenv() #위에 있어야 오류x

from fastapi import FastAPI
from .routers import home, users, foods, auth, ai

app = FastAPI()

# 라우터 등록
app.include_router(auth.router)
app.include_router(home.router)
app.include_router(users.router)
# app.include_router(foods.router) 
# -> ai.router 에서 처리하는 듯해 삭제(ai 코드 작성 전 임의로 작성한 코드)
app.include_router(ai.router) 

@app.get("/", tags=["루트"])
async def root():
    """
    ## Food Analyzer MVP API (리팩토링 버전)
    
    ### 핵심 기능:
    - **인증**: `/api/auth/me` - 토큰 검증 + 유저 upsert
    - **홈화면**: `/api/home` - 사용자 요약 + 현재 국가 Top3
    - **음식 해석**: `/api/foods/interpret` - OCR/번역 → AI 음식 설명
    - **사용자**: `/api/users/me` - 프로필 조회/수정
    - **저장**: `/api/users/me/saved-foods` - 저장 목록/생성/삭제
    
    ### 시작하기:
    1. `/docs`에서 API 문서 확인
    2. `/api/auth/me`으로 Firebase ID Token으로 인증
    3. 음식 사진 업로드 및 AI 해석
    4. 음식 설명 저장 및 관리
    """
    return {
        "endpoints": {
            "인증": "/api/auth/me",
            "홈화면": "/api/home",
            "음식 해석": "/api/foods/interpret",
            "사용자": "/api/users/me",
            "저장 관리": "/api/users/me/saved-foods"
        }
    }