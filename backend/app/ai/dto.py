from typing import List, Optional
from pydantic import BaseModel, Field

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

class AnalyzeOneResponse(BaseModel):
    data: dict
