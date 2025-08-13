import os, json, asyncio, time, logging
from typing import Dict, List
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from google import genai
from backend.app.ai.dto import AnalyzeOneRequest
from backend.app.ai.image_fetcher import fetch_dish_image_url_async
from backend.app.models.food import FoodInfo

load_dotenv()

MAX_TOKENS = 3000
GENAI_API_KEY = os.getenv("GOOGLE_API_KEY")
SERVICE_ACCOUNT = os.getenv("FIREBASE_CREDENTIALS")
MODEL_NAME = "gemini-2.5-flash" # "gemini-1.5-pro", "gemini-2.0-pro-exp", "gemini-2.5-flash"
COUNTRY_ENUM = ['CN', 'ES', 'FR', 'IT', 'JP', 'KR', 'MX', 'TH', 'US', 'VN']
ALLERGEN_ENUM = [
    'BEEF','BUCKWHEAT','CHICKEN','CRAB','EGG','MACKEREL','MILK','PEACH',
    'PEANUT','PINE_NUT','PORK','SHELLFISH','SHRIMP','SOY','SQUID',
    'SULFITES','TOMATO','WALNUT','WHEAT'
]

logger = logging.getLogger(__name__)
if not firebase_admin._apps:
    cred = credentials.Certificate(SERVICE_ACCOUNT)
    firebase_admin.initialize_app(cred)

db = firestore.client()
client = genai.Client(api_key=GENAI_API_KEY)

# User의 식성정보읽어오기 
def extract_user_constraints(user_profile) -> Dict:
    allergies = user_profile.allergies if user_profile else []
    diet = user_profile.dietaryRestrictions if user_profile else None
    religion = ", ".join(diet) if isinstance(diet, list) else (diet or None)
    return {"allergies": allergies, "religion": religion}

def build_prompt(*, food_name: str, country_hint: str | None,
                 target_lang_code: str, allergies: List[str], religion: str | None) -> str:
    country_enum = ", ".join(COUNTRY_ENUM)
    allergen_enum = ", ".join(ALLERGEN_ENUM)

    return f"""
    You are analyzing information about a specific dish: "{food_name}".
    Respond ONLY in JSON that conforms to the schema below. Do NOT include code fences.
    Language rules (STRICT):
    - The "country" field MUST be in English only (choose from: {country_enum}). If unknown, use "".
    - The "allergens" array MUST be in English only, using only canonical values from: {allergen_enum}. If unknown, use [].
    - All other fields (dishName, ingredients, summary, recommendations, culturalBackground) MUST be entirely in {target_lang_code}.
    - Never mix languages inside a single field.
    Schema:
    {{
    "country": "<{country_enum}> or \"\"",
    "dishName": "<{target_lang_code}>",
    "ingredients": ["{target_lang_code} 3~5 words"],                
    "allergens": ["{allergen_enum}"],      
    "summary": "<{target_lang_code} 2 sentences>",
    "recommendations": ["{target_lang_code} ..."],
    "culturalBackground": "<{target_lang_code} 2 sentences>"
    }}

    User constraints:
    - allergies: {", ".join(allergies) if allergies else "none"}
    - religion/diet: {religion or "none"}
    Country constraints:
    - This dish is likely from {country_hint} (cuisine_country_code).
    - This dish is NOT from {target_lang_code} (cuisine_country_code).
    """.strip()

def safe_load_json(text: str) -> Dict:
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t.lower().startswith("json"):
            t = t[4:].strip()
    return json.loads(t)

def validate_and_normalize(obj: Dict) -> Dict:
    required = [
        "country","dishName","ingredients","allergens",
        "summary","recommendations","culturalBackground"
    ]
    for k in required:
        if k not in obj:
            raise ValueError(f"Missing key: {k}") # 빠진 키가 있는지 

    to_str = lambda v: "" if v is None else str(v).strip()
    def uniq(xs): return list(dict.fromkeys(xs))
    def str_list(v):
        if not isinstance(v, list): return []
        return uniq([to_str(x) for x in v if to_str(x)])

    # 문자열 필드 정리
    obj["dishName"] = to_str(obj.get("dishName"))
    obj["summary"] = to_str(obj.get("summary"))
    obj["culturalBackground"] = to_str(obj.get("culturalBackground"))
    # 배열 필드 정리
    obj["ingredients"] = str_list(obj.get("ingredients"))
    obj["recommendations"] = str_list(obj.get("recommendations"))

    # country 제약
    raw_country = to_str(obj.get("country"))
    obj["country"] = raw_country if raw_country in COUNTRY_ENUM else ""

    # allergens 제약(대소문자/복수형 보정 → 카논 상수로 매핑)
    canon = {v.lower(): v for v in ALLERGEN_ENUM}
    def norm_allergen(a: str):
        lower = a.strip().lower()
        if lower.endswith("s") and lower[:-1] in canon:
            lower = lower[:-1]
        return canon.get(lower)
    raws = str_list(obj.get("allergens"))
    obj["allergens"] = [x for x in uniq([norm_allergen(a) for a in raws]) if x]
    return obj

# 동기함수 로직 스레드로 off-load
async def _to_thread(fn, *args, **kwargs):
    return await asyncio.to_thread(fn, *args, **kwargs)

async def timed_task(coro, label):
    t0 = time.time()
    result = await coro
    elapsed = time.time() - t0
    print(f"{label} took {elapsed:.3f} sec")
    return result

async def analyze_one_async(
    cons: Dict, req: AnalyzeOneRequest,
) -> Dict:
    item = req.food_name # 음식명 
    logging.info('item : %s',item)

    prompt = build_prompt(  # prompt 빌드 
        food_name=item,
        country_hint=req.source_language,
        target_lang_code= req.target_language,
        allergies=cons.get("allergies", []),
        religion=cons.get("religion"),
    )

    # t0 = time.time()
    # resp = await client.aio.models.generate_content( # Gemini async 호출 
    #     model=MODEL_NAME,
    #     contents=prompt,
    #     config={
    #         "temperature": 0.4,
    #         "max_output_tokens": MAX_TOKENS,
    #         "response_mime_type": "application/json",
    #     },
    # )
    # logging.info("Vision DOC_OCR: %.3fs", time.time() - t0) 
    img_task = asyncio.create_task(
        timed_task(fetch_dish_image_url_async(item, req.source_language), "Image fetch")
    )
    llm_task = asyncio.create_task(
        timed_task(
            client.aio.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config={
                    "temperature": 0.4,
                    "max_output_tokens": MAX_TOKENS,
                    "response_mime_type": "application/json",
                },
            ),
            "LLM call"
        )
    )
    resp, first_img_url = await asyncio.gather(llm_task, img_task)

    text = ""
    if resp.candidates and resp.candidates[0].content.parts:
        part = resp.candidates[0].content.parts[0]
        text = getattr(part, "text", "") or getattr(part, "inline_data", {}).get("data", "")
    if not text:
        fr = getattr(resp.candidates[0], "finish_reason", "UNKNOWN") if resp.candidates else "NO_CANDIDATE"  # fallback: finish_reason 확인 메시지
        return {"foodName": item, "error": f"empty response (finish_reason={fr})"}

    try:
        raw = json.loads(text)
    except Exception:
        raw = safe_load_json(text) # 모델이 fence를 넣었거나 잡다한 문구가 끼면 기존 안전 파서 사용
    data = validate_and_normalize(raw)
    image_source = 'Crawling' if first_img_url is not None else 'None'
    # t1 = time.time()
    # # url = await _to_thread(fetch_dish_image_url, data.get("dishName") or item, req.source_language)
    # logging.info("Vision DOC_OCR: %.3fs", time.time() - t1) 
    ai_results = {"foodName": item, "imageUrl": first_img_url, "imageSource" : image_source, **data}
    info = FoodInfo.model_validate(ai_results)
    return info
