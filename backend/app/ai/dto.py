from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.food import FoodInfo

# ---------- OCR ----------
class OCRWord(BaseModel):
    text: str
    cx: float
    cy: float

# ---------- Translate ----------
class MenuItemOut(BaseModel):
    text: str
    translated: str
    cx: float
    cy: float

# ---------- Analyze One ----------
class AnalyzeOneRequest(BaseModel):
    source_language: str = Field(..., description="음식의 원산지에 대한 설명")
    target_language: str = Field(..., description="음식에 대한 분석을 target_lanugage로 작성")
    food_name: str = Field(..., description="translated된 이름이 아닌 원어가 들어와야함")
    country: Optional[str] = Field(None, description="국가 코드 (예: JP, KR)")

class AnalyzeOneResponse(BaseModel):
    data: FoodInfo
    is_from_cache: bool = False  # 기존 검색 결과에서 가져온 것인지 여부
    personalized_info: Optional[Dict[str, Any]] = None  # 개인화된 정보 (알레르기 경고 등)
