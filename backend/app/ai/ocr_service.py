# ocr_service.py
from collections import Counter
import os, re, time, logging, cv2, json
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from google.cloud import vision
from google.oauth2 import service_account
from statistics import median
from backend.app.ai.image_preprocess import preprocess_image

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

cred_json = os.getenv("GOOGLE_OCR_CREDENTIALS")  
info = json.loads(cred_json)
creds = service_account.Credentials.from_service_account_info(info)
client = vision.ImageAnnotatorClient(credentials=creds)

# 비슷한 y좌표의 글자끼리 묶기 
def group_lines_by_y(tokens, y_alpha=0.65, min_tol=6.0, header_cut=2.2):
    g_h_med_all = median(t["h"] for t in tokens) # 헤더 컷(아주 큰 글자 제거) 후 전역 높이 중앙값 재추정
    toks = [t for t in tokens if t["h"] <= header_cut * g_h_med_all] or tokens
    g_h_med = median(t["h"] for t in toks)

    base_tol = max(min_tol, g_h_med * y_alpha) # 버킷 사이즈를 전역 높이 중앙값
    bucket_size = base_tol

    def bucket_id(y):
        return int(y // bucket_size)

    lines = []  
    buckets = {}  

    for t in toks:
        bid = bucket_id(t["cy"])
        candidate_line_idxs = []
        for b in (bid - 1, bid, bid + 1):  # 인접 버킷(±1)만 관찰
            candidate_line_idxs.extend(buckets.get(b, []))

        best_i, best_dy = None, None

        for i in candidate_line_idxs:
            L = lines[i]
            h_med_line = median(L["hs"]) if L["hs"] else g_h_med
            tol = max(min_tol, h_med_line * y_alpha)
            dy = abs(t["cy"] - L["y"])
            if dy <= tol and (best_dy is None or dy < best_dy):
                best_i, best_dy = i, dy

        if best_i is None: # 새 라인 생성 + 버킷 등록
            new_idx = len(lines)
            lines.append({"items": [t], "y": t["cy"], "hs": [t["h"]]})
            buckets.setdefault(bid, []).append(new_idx)
        else: # 기존 라인에 추가하고 러닝 평균 갱신
            L = lines[best_i]
            L["items"].append(t)
            old_bid = bucket_id(L["y"])
            L["y"] = 0.7 * L["y"] + 0.3 * t["cy"]  # EMA로 안정화
            L["hs"].append(t["h"])
            new_bid = bucket_id(L["y"])
            if new_bid != old_bid:
                if old_bid in buckets:
                    buckets[old_bid] = [idx for idx in buckets[old_bid] if idx != best_i]
                    if not buckets[old_bid]:
                        buckets.pop(old_bid, None)
                buckets.setdefault(new_bid, []).append(best_i)

    return lines

# x좌표 고려하여 이어붙이거나 분리 
def merge_line_by_x(line_tokens, x_alpha=1.6, join_with_space=False):
    gaps = []
    for a, b in zip(line_tokens, line_tokens[1:]): # 라인의 인접 x 간격 분포 계산
        gaps.append(max(0.0, b['cx'] - a['cx']))
    gap_med = median(gaps) if gaps else (median([t['h'] for t in line_tokens]) * 0.6)
    gap_th = gap_med * x_alpha

    words = []
    buf = [line_tokens[0]]
    def is_number_token(token_text):
        return re.fullmatch(r"\d+(\.\d+)?", token_text) is not None
    
    for prev, cur in zip(line_tokens, line_tokens[1:]):
        dx = cur['cx'] - prev['cx']
        if is_number_token(cur['text']):
            if buf:
                text = "".join(t['text'] for t in buf) if not join_with_space else " ".join(t['text'] for t in buf)
                cx = median(t['cx'] for t in buf)
                cy = median(t['cy'] for t in buf)
                words.append({"text": text, "cx": cx, "cy": cy})
            buf = []  # 숫자 토큰은 추가하지 않고 buf 초기화
            continue
        if dx <= gap_th: # 같은 단어로 이어붙임
            buf.append(cur) 
        else: # 다른 단어로 분리 
            text = "".join(t['text'] for t in buf) if not join_with_space else " ".join(t['text'] for t in buf)
            cx = median(t['cx'] for t in buf)
            cy = median(t['cy'] for t in buf)
            words.append({"text": text, "cx": cx, "cy": cy})
            buf = [cur]
    if buf:
        text = "".join(t['text'] for t in buf) if not join_with_space \
            else " ".join(t['text'] for t in buf)
        cx = median(t['cx'] for t in buf)
        cy = median(t['cy'] for t in buf)
        words.append({"text": text, "cx": cx, "cy": cy})
    return words

def group_menu_items(words):
    lines = group_lines_by_y(words)
    merged_words = []
    for line in lines:
        merged_words.extend(merge_line_by_x(line["items"], x_alpha=1.6, join_with_space=False))
        
    filtered_words = []
    for w in merged_words:
        text = w["text"]
        if re.fullmatch(r"\d+(\.\d+)?", text): # 숫자가 포함된 토큰 제거
            continue
        if re.search(r"[.:,/]", text):
            continue
        cleaned = re.sub(r"\d+(\.\d+)?", "", text) # 글자+숫자 혼합이면 숫자만 제거
        cleaned = cleaned.strip()
        if cleaned and len(cleaned) > 1:  # 1글자도 제외
            w["text"] = cleaned
            filtered_words.append(w)

    return filtered_words

# def annotate_words_on_image(image_input, words, out_path="annotated.png",
#                             font_path=None, font_size=50):
#     img = PILImage.open(BytesIO(image_input)).convert("RGB")
#     font = ImageFont.load_default()
#     draw = ImageDraw.Draw(img)

#     for w in words:
#         x = int(round(w["cx"])); y = int(round(w["cy"]))
#         r = max(3, int(round((w.get("h", 16) or 16) * 0.2)))
#         draw.ellipse((x-r, y-r, x+r, y+r), outline=(0,0,0), width=10)
#         label = w["text"]
#         if isinstance(font, ImageFont.ImageFont):  # load_default일 때
#             scale = 2  # 기본 2배
#             label_img = PILImage.new("RGB", (len(label)*8*scale, 11*scale), (255, 255, 255))
#             tmp_draw = ImageDraw.Draw(label_img)
#             tmp_draw.text((0, 0), label, font=font, fill=(0, 0, 0))  # 검은색 글씨
#             img.paste(label_img, (x, y - 11*scale - 6))
#     img.save(out_path)

def detect_menu(image_bytes: bytes):
    img = preprocess_image(image_bytes, rectify=True) # np.ndarray (BGR)

    ok, buf = cv2.imencode(".png", img) # Vision에 넣을 PNG 바이트로 인코드
    if not ok:
        raise RuntimeError("Failed to encode image to PNG")
    png_bytes = buf.tobytes()
    
    t0 = time.time()
    resp = client.document_text_detection(image=vision.Image(content=png_bytes))
    logging.info("Vision DOC_OCR: %.3fs", time.time() - t0)

    if resp.error.message:
        raise RuntimeError(resp.error.message)

    lang_counts = Counter()
    words: List[Dict] = []

    fta = resp.full_text_annotation
    for page in fta.pages:
        for block in page.blocks:
            for para in block.paragraphs:
                for w in para.words:
                    # 언어 집계
                    if getattr(w, "property", None) and getattr(w.property, "detected_languages", None):
                        for l in w.property.detected_languages:
                            if l.language_code:
                                lang_counts[l.language_code] += 1
                    # 단어 좌표 (원하면 유지)
                    txt = "".join([s.text for s in w.symbols if s.text])
                    box = w.bounding_box.vertices
                    xs = [v.x for v in box]; ys = [v.y for v in box]
                    cx = sum(xs) / 4.0; cy = sum(ys) / 4.0
                    h  = (max(ys) - min(ys)) or 1
                    words.append({"text": txt, "cx": cx, "cy": cy, "h": h})

    top_lang = (lang_counts.most_common(1)[0][0].upper()) if lang_counts else None
    final_words = group_menu_items(words)
    print('words : ', final_words)
    return final_words, top_lang
