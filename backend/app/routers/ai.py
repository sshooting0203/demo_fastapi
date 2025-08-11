import asyncio, time, logging
from fastapi import APIRouter, HTTPException, UploadFile, Form, File
from typing import List, Optional
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.app.ai.food_analyzer import _to_thread, extract_user_constraints, analyze_one_async
from backend.app.ai.translate_food import translate_async
from backend.app.ai.ocr_service import detect_menu
from backend.app.services.user_service import user_service
import httpx
from backend.app.ai.dto import (
    AnalyzeOneRequest, AnalyzeOneResponse, MenuItemOut,
)
from backend.app.models import SaveFoodRequest
from backend.app.routers.auth import get_current_user
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

    try:
        data = await analyze_one_async(cons, req)
        # logging.info("data results : %s", data)
        await user_service.increase_search_count(data)
        # 메타데이터 검색 횟수 증가 (저장은 안함)
        return AnalyzeOneResponse(data=data)
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
