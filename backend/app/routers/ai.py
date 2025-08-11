import asyncio, time, logging
from fastapi import APIRouter, HTTPException, UploadFile, Form, File
from typing import List, Optional
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.ai.food_analyzer import _to_thread, extract_user_constraints, analyze_one_async
from app.ai.translate_food import translate_async
from app.ai.ocr_service import detect_menu
from app.services.user_service import user_service
import httpx
from app.ai.dto import (
    AnalyzeOneRequest, AnalyzeOneResponse, MenuItemOut,
)
from app.models import SaveFoodRequest
from app.routers.auth import get_current_user
from fastapi import APIRouter, HTTPException, UploadFile, Form, File, Depends
from typing import List, Optional, Dict

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["ai를 사용하여 음식에 대한 ocr, translate, analyze"])

ALLOWED_CT = {"image/png", "image/jpeg"} # 이미지 허용 포맷 
MAX_BYTES = 5 * 1024 * 1024  # 이미지 최대 허용 크기5MB

@router.post("/analyze", response_model=AnalyzeOneResponse)
async def analyze_one(req: AnalyzeOneRequest, current_user: dict = Depends(get_current_user)):
    uid = current_user["uid"]
    user = await user_service.get_user_profile(uid)  #여기 수정(변경됨)
    cons = extract_user_constraints(user or {})
    
    logger.info(f"음식 분석 요청 시작: {req.food_name} (국가: {req.country})")

    try:
        # 1단계: 기존 검색 결과에서 동일한 쿼리 확인
        from app.services.search_service import search_service
        
        logger.info(f"기존 검색 결과 확인 중...")
        # OCR/번역된 원어 음식명으로 기존 결과 검색
        existing_result = await search_service.find_existing_search_result(
            query=req.food_name,  # 원어 음식명
            country=req.country
        )
        
        if existing_result:
            logger.info(f"기존 검색 결과 발견! AI 분석 건너뜀: {existing_result['doc_id']}")
            logger.info(f"기존 결과 데이터 구조: {existing_result['data']}")
            
            # 2단계: 사용자 정보로 개인화
            personalized_result = await search_service.personalize_search_result(
                search_result=existing_result['data'],
                user_allergies=user.allergies if user else [],
                user_dietary=user.dietaryRestrictions if user else []
            )
            
            # 3단계: 검색 횟수만 증가 (AI 분석은 하지 않음)
            # 기존 검색 결과에서 FoodInfo 객체 생성
            from app.models.food import FoodInfo
            
            # 데이터 구조 확인 및 필수 필드 보완
            food_data = existing_result['data']['data'].copy()
            
            # foodName이 없으면 foodName 필드에서 가져오기
            if 'foodName' not in food_data and 'foodName' in existing_result['data']:
                food_data['foodName'] = existing_result['data']['foodName']
            
            # 필수 필드가 없으면 기본값 설정
            required_fields = ['foodName', 'dishName', 'country', 'summary', 'recommendations', 'ingredients', 'allergens']
            for field in required_fields:
                if field not in food_data:
                    logger.warning(f"필수 필드 누락: {field}, 기본값 설정")
                    if field == 'foodName':
                        food_data[field] = existing_result['data'].get('foodName', '알 수 없는 음식')
                    elif field == 'dishName':
                        food_data[field] = existing_result['data'].get('dishName', '알 수 없는 음식')
                    elif field == 'country':
                        food_data[field] = existing_result['data'].get('country', 'UN')
                    elif field in ['summary', 'recommendations', 'ingredients', 'allergens']:
                        food_data[field] = []
            
            logger.info(f"FoodInfo 생성용 데이터: {food_data}")
            existing_food_info = FoodInfo(**food_data)
            
            # 개인화된 정보 반영 (안전한 추천 항목 등)
            if personalized_result.get('personalized', {}).get('safe_recommendations'):
                existing_food_info.recommendations = personalized_result['personalized']['safe_recommendations']
            
            await user_service.increase_search_count(existing_food_info)
            
            # 4단계: 개인화된 결과 반환
            logger.info(f"기존 결과 + 개인화 완료 (AI 분석 없음)")
            return AnalyzeOneResponse(
                data=existing_food_info,
                is_from_cache=True,
                personalized_info=personalized_result.get('personalized', {})
            )
        
        # 기존 결과가 없으면 AI 분석 진행
        logger.info(f"기존 검색 결과 없음, AI 분석 시작: {req.food_name}")
        data = await analyze_one_async(cons, req)
        
        # 검색 결과 저장
        await search_service._save_search_result(uid, req.food_name, f"{data.country}_{data.foodName}", data)
        
        # 메타데이터 검색 횟수 증가
        await user_service.increase_search_count(data)
        
        logger.info(f"AI 분석 완료. 새 결과 저장됨")
        return AnalyzeOneResponse(data=data, is_from_cache=False)
        
    except Exception as e:
        logger.exception("analyze-one failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ocr-translate", response_model=List[MenuItemOut])
async def ocr_translate(
    target_language: str = Form(..., description="번역 대상 언어 코드(KR,EN)"),
    file: Optional[UploadFile] = File(None, description="이미지 파일 (multipart/form-data)"),
    image_url: Optional[str] = Form(None, description="이미지 URL"),
    current_user: Optional[dict] = Depends(get_current_user)
) -> List[MenuItemOut] :
    
    uid = current_user.get('uid') if current_user else None
    if uid is None: 
        raise HTTPException(status_code=401, detail="User not registered")
    
    try:
        data = await read_image_bytes(file, image_url)
        words, lang = detect_menu(data)
        # logger.info("Detected Language: %s", lang)
        logger.info("Detected Words: %s", words)
    except Exception as e:
        logger.exception("OCR failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    
    try:
        translated = await translate_async(words, target_language)
    except Exception as e:
        logger.exception("Translate failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    # logger.info('translated : %s',translated)
    return translated

async def read_image_bytes(file: Optional[UploadFile], image_url: Optional[str]) -> bytes:
    if file: 
        if file.content_type not in ALLOWED_CT:
            raise HTTPException(status_code=415, detail=f"Unsupported Content-Type: {file.content_type}")
        data = await file.read()
        if len(data) > MAX_BYTES:
            raise HTTPException(status_code=413, detail="Image too large (max 5MB).")
        return data

    async with httpx.AsyncClient(timeout=15) as client: # file가 없으면 URL 모드라고 가정하고 비동기 HTTP 클라이언트로 이미지를 다운로드
        r = await client.get(image_url, follow_redirects=True)
        r.raise_for_status()
        data = r.content
        
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Image too large (max 5MB).")
    return data
