# app/ai/translate_one.py
import os, json, asyncio, logging
from typing import Dict, List, Optional
from dotenv import load_dotenv
from google import genai

load_dotenv()
GENAI_API_KEY = os.getenv("GOOGLE_API_KEY")
SERVICE_ACCOUNT = os.getenv("FIREBASE_CREDENTIALS")
MODEL_NAME = "gemini-2.5-flash" 
MAX_TOKENS = 2000

logger = logging.getLogger(__name__)
client = genai.Client(api_key=GENAI_API_KEY)

def _build_prompt(words: List[str], target_lang: str) -> str:
    bullets = "\n".join(f"- {w}" for w in words)
    return f"""
    You are judging whether each TOKEN is food and provide a natural interpretation of it.
    Respond ONLY in JSON that conforms to the schema below. Do NOT include code fences.
    Schema:
    {{
    "text": "<original TOKEN EXACTLY>",
    "is_food": true/false,
    "translated": "<{target_lang} if is_food=true, else empty>",
    }}
    Constraints:
    - Keep array length and ORDER exactly as input.
    - Keep "text" EXACTLY as given.
    - Prices (e.g., "7.30"), sizes (S/M/L), counts, categories ("Beverage","Dessert"), vague words ("special","fresh") are NOT food.
    - Numerals/punctuation-only are NOT food.
    - If unsure, set is_food=false and translated="".
    TOKENS: {bullets}
    """.strip()

def safe_load_json(text: str) -> Dict:
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t.lower().startswith("json"):
            t = t[4:].strip()
    return json.loads(t)

def _align(outputs, inputs: List[str]) -> List[Dict]:
    if isinstance(outputs, list) and len(outputs) == len(inputs):
        out = []
        for w, o in zip(inputs, outputs):
            is_food = bool(o.get("is_food", False))
            translated = (o.get("translated") or "").strip() if is_food else ""
            score = o.get("score", None)
            try:
                score = float(score) if score is not None else None
                if score is not None: score = max(0.0, min(1.0, score))
            except Exception:
                score = None
            out.append({"text": w, "is_food": is_food, "translated": translated, "score": score})
        return out
    by_text = {str(o.get("text","")).strip(): o for o in (outputs or [])}
    out = []
    for w in inputs:
        o = by_text.get(w.strip())
        if not o:
            out.append({"text": w, "is_food": False, "translated": "", "score": None})
        else:
            is_food = bool(o.get("is_food", False))
            translated = (o.get("translated") or "").strip() if is_food else ""
            score = o.get("score", None)
            try:
                score = float(score) if score is not None else None
                if score is not None: score = max(0.0, min(1.0, score))
            except Exception:
                score = None
            out.append({"text": w, "is_food": is_food, "translated": translated, "score": score})
    return out

async def translate_async(words: List[str], target_language: str) -> List[Dict]:
    if not words:
        return []
    prompt = _build_prompt(words, target_language)
    resp = await client.aio.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config={
            "temperature": 0.1,
            "max_output_tokens": MAX_TOKENS,
            "response_mime_type": "application/json",
        },
    )
    # logger.info("reps: %s", resp)
    text = ""
    if resp.candidates and resp.candidates[0].content.parts:
        p = resp.candidates[0].content.parts[0]
        text = getattr(p, "text", "") or getattr(p, "inline_data", {}).get("data", "")
    if not text:
        return [{"text": w, "is_food": False, "translated": "", "score": 0.0} for w in words]
    try:
        raw = json.loads(text)
    except Exception:
        raw = safe_load_json(text) 

    # logger.info('words : %s', words)
    # logger.info('raw : %s', raw)

    foods = []
    for w in words:
        match = next((o for o in raw if o.get("text") == w.get("text") and o.get("is_food")), None)
        if match:
            foods.append({
                "text": match["text"],
                "translated": match.get("translated", ""),
                "cx": w.get("cx"),
                "cy": w.get("cy"),
            })
    return foods