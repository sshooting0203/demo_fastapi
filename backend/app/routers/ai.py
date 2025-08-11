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

from app.ai.food_analyzer import convert_ai_result_to_food_info
from app.models.food import SaveFoodRequest
from app.routers.auth import get_current_user
from fastapi import APIRouter, HTTPException, UploadFile, Form, File, Depends
from typing import List, Optional, Dict
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth, firestore
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/food", tags=["ai를 사용하여 음식에 대한 ocr, translate, analyze"])

ALLOWED_CT = {"image/png", "image/jpeg"} # 이미지 허용 포맷 
MAX_BYTES = 5 * 1024 * 1024  # 이미지 최대 허용 크기5MB

@router.post("/analyze", response_model=AnalyzeOneResponse)
async def analyze_one(req: AnalyzeOneRequest):
    user = await user_service.get_user_profile(req.uid)  #여기 수정(변경됨)
    cons = extract_user_constraints(user or {})

    try:
        data = await analyze_one_async(cons, req)
        #!!!!!!!!!!!!!!!!!!! AI 결과를 FoodInfo로 변환
        food_info = convert_ai_result_to_food_info(data)
        # 메타데이터 검색 횟수 증가 (저장은 안함)
        await user_service.increase_search_count(food_info)
        
        return AnalyzeOneResponse(data=data)
    except Exception as e:
        logger.exception("analyze-one failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ocr-translate", response_model=List[MenuItemOut])
async def ocr_translate(
    target_language: str = Form(..., description="번역 대상 언어 코드(KR,EN)"),
    file: Optional[UploadFile] = File(None, description="이미지 파일 (multipart/form-data)"),
    image_url: Optional[str] = Form(None, description="이미지 URL"),
) -> List[MenuItemOut] :
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

# 음식 저장 여기로 추가
# 무조건 ai 검색 후 저장 가능하니
async def increase_save_count(self, uid: str) -> bool:
    """사용자의 저장횟수 증가"""
    try:
        user_ref = self.db.collection('users').document(uid)
        
        @firestore.transactional
        def update_save_count(transaction, user_ref):
            user_doc = user_ref.get(transaction=transaction)
            if not user_doc.exists:
                raise Exception(f"사용자를 찾을 수 없습니다: {uid}")
            
            current_save_count = user_doc.to_dict().get('saveCount', 0)
            new_save_count = current_save_count + 1
            
            transaction.update(user_ref, {
                'saveCount': new_save_count,
                'updatedAt': datetime.now()
            })
            
            return new_save_count
        
        transaction = self.db.transaction()
        new_count = update_save_count(transaction, user_ref)
        
        logger.info(f"사용자 {uid}의 저장횟수 증가: {new_count}")
        return True
        
    except Exception as e:
        logger.error(f"저장횟수 증가 실패: {str(e)}")
        return False