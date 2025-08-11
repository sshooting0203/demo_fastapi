# image_fetcher.py
import re, time, random, asyncio, os
from typing import List, Optional, Iterable, Set
from urllib.parse import urlencode, urlparse
from dotenv import load_dotenv
import aiohttp 
# request(동) 쓰지 않고 aiohttp(비동기)
from bs4 import BeautifulSoup

load_dotenv()

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
UNSPLASH_ACCESS_KEY=os.getenv('UNSPLASH_ACCESS_KEY')

def _h() -> dict:
    return {"User-Agent": _UA, "Accept-Language": "en-US,en;q=0.9"}

def _h_api() -> dict:
    return {
        "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}",
        "Accept-Version": "v1",
        "User-Agent": _UA,
    }

_BLOCKED = {
    "wikipedia.org", "wikimedia.org", "commons.wikimedia.org", "upload.wikimedia.org", "gstatic.com"
}

def _is_blocked(u: str) -> bool:
    try:
        host = (urlparse(u).hostname or "").lower()
        return any(host == d or host.endswith("." + d) for d in _BLOCKED)
    except Exception:
        return True

def _looks_like_real_image(u: str) -> bool:
    low = u.lower()
    if low.endswith((".svg", ".gif")):  # 가벼운 제외 규칙만 유지
        return False
    if any(k in low for k in ("sprite", "icon", "logo")):
        return False
    return True

# --- 이미지 URL 검증 ---
async def _is_image(session, u, timeout_sec=8.0):
    timeout = aiohttp.ClientTimeout(total=timeout_sec)
    try:
        async with session.head(u, headers=_h(), allow_redirects=True, timeout=timeout) as r:
            ct = r.headers.get("content-type", "")
            if r.status == 200 and ct.startswith("image/"):
                return True
    except:
        pass
    try:
        async with session.get(u, headers=_h(), allow_redirects=True, timeout=timeout) as r:
            ct = r.headers.get("content-type", "")
            return r.status == 200 and ct.startswith("image/")
    except:
        return False


# --- Bing 이미지 후보 수집 (murl만) ---
_MURL_RE = re.compile(r'"murl":"(.*?)"')
async def _bing_images(session: aiohttp.ClientSession, q: str, limit: int = 6) -> List[str]:
    url = "https://www.bing.com/images/search?" + urlencode({"q": q})
    try:
        async with session.get(url, headers=_h(), timeout=aiohttp.ClientTimeout(total=8)) as resp:
            html = await resp.text()
    except Exception:
        return []

    soup = BeautifulSoup(html, "html.parser")
    out: Set[str] = set()

    for a in soup.select("a.iusc"):
        raw = a.get("m") or a.get("data-m")
        if not raw:
            continue
        m = _MURL_RE.search(raw)
        if m:
            u = m.group(1).replace("\\u002f", "/").replace("\\", "")
            out.add(u)

    cand = [u for u in out if not _is_blocked(u) and _looks_like_real_image(u)]
    return cand[:limit]

# --- 첫 유효 이미지 즉시 반환 ---
async def _first_ok(session: aiohttp.ClientSession, urls: Iterable[str], concurrency: int = 10) -> str:
    sem = asyncio.Semaphore(concurrency)

    async def check(u: str):
        async with sem:
            return u if await _is_image(session, u) else ""

    tasks = [asyncio.create_task(check(u)) for u in urls]
    try:
        for fut in asyncio.as_completed(tasks):
            res = await fut
            if res:
                for t in tasks:
                    if not t.done(): t.cancel()
                return res
    finally:
        await asyncio.gather(*tasks, return_exceptions=True)
    return ""

async def _unsplash_images(session: aiohttp.ClientSession, q: str, per_page: int = 10) -> List[str]:
    if not UNSPLASH_ACCESS_KEY:
        return []
    params = {
        "query": q,
        "per_page": per_page,
        "content_filter": "high",   # 성인/민감도 필터
        "orientation": "landscape", # 음식 전시용 가로 이미지 선호 시
    }
    url = "https://api.unsplash.com/search/photos?" + urlencode(params)
    try:
        async with session.get(url, headers=_h_api(), timeout=aiohttp.ClientTimeout(total=8)) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()
    except Exception:
        return []

    out: List[str] = []
    for item in data.get("results", []):
        # urls: raw, full, regular, small, thumb
        u = item.get("urls", {}).get("regular") or item.get("urls", {}).get("full")
        if u:
            out.append(u)
    return out

async def fetch_dish_image_url_async(dish_name: str, country_hint: str=None, per_query_limit=6, validate_concurrency=12) -> str:
    queries = [dish_name]
    if country_hint:
        queries.insert(0, f"{dish_name} {country_hint}")
    queries += [f"{dish_name} dish", f"{dish_name} food"]

    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=10),
        connector=aiohttp.TCPConnector(ssl=False, limit=0),
    ) as session:
        bing_tasks = [asyncio.create_task(_bing_images(session, q, limit=per_query_limit)) for q in queries] #  Bing 검색 병렬 실행
        results = await asyncio.gather(*bing_tasks)
        all_urls = []
        seen = set()
        for urls in results:
            for u in urls:
                if u not in seen:
                    seen.add(u)
                    all_urls.append(u)
        return await _first_ok(session, all_urls, concurrency=validate_concurrency)

    # async with aiohttp.ClientSession(
    #     timeout=aiohttp.ClientTimeout(total=12),
    #     connector=aiohttp.TCPConnector(limit=0),
    # ) as session:
    #     # 쿼리 우선순위를 지키기 위해 '순차'로 조회 후 첫 결과를 리턴
    #     seen = set()  
    #     for q in queries:
    #         urls = await _unsplash_images(session, q, per_page=per_query_limit)  # List[str]
    #         for u in urls:
    #             if u and u not in seen:
    #                 return u  # ← 첫 유효 이미지 URL만 리턴
    #             seen.add(u)
    # return ""