from typing import Optional, Dict
from ..db.firestore_client import firestore_client

class HomeService:
    # ---------- 핵심 헬퍼(양방향) ----------
    def _get_country_by_code(self, code: str) -> Optional[Dict]:
        """CODE -> {code, name, nameKo, flag}"""
        if not code:
            return None
        code = code.strip().upper()
        doc = firestore_client.db.collection("country").document(code).get()
        if not doc.exists:
            return None
        data = doc.to_dict() or {}
        return {"code": code, "name": data.get("name"), "nameKo": data.get("nameKo"), "flag": data.get("flag")}

    def _get_country_by_name(self, name: str) -> Optional[Dict]:
        """nameKo/name -> {code, name, nameKo, flag}"""
        if not name:
            return None
        name = name.strip()
        col = firestore_client.db.collection("country")

        # 한글명 우선
        docs = col.where("nameKo", "==", name).limit(1).get()
        if docs:
            d = docs[0]; data = d.to_dict() or {}
            return {"code": d.id, "name": data.get("name"), "nameKo": data.get("nameKo"), "flag": data.get("flag")}

        # 영문명 대체
        docs = col.where("name", "==", name).limit(1).get()
        if docs:
            d = docs[0]; data = d.to_dict() or {}
            return {"code": d.id, "name": data.get("name"), "nameKo": data.get("nameKo"), "flag": data.get("flag")}

        return None

    # ---------- 등록: DB에는 code만 저장 ----------
    def register_travel_country(self, uid: str, country_code: str | None = None, country_name: str | None = None) -> Dict:
        """
        요청은 code 또는 name 허용(문서 스펙).
        내부 저장은 항상 users/{uid}.currentCountry = KR (대문자 고정).
        응답은 {code,name} (문서 스펙).
        """
        country = None
        if country_code:
            country = self._get_country_by_code(country_code)
        if not country and country_name:
            country = self._get_country_by_name(country_name)

        if not country:
            raw = country_code or country_name or ""
            raise ValueError(f"지원하지 않는 국가입니다: {raw}")

        # set(merge)로 안전 저장
        firestore_client.db.collection("users").document(uid).set(
            {"currentCountry": country["code"]}, merge=True
        )
        # 응답은 영문 name 우선(없으면 nameKo)
        return {"code": country["code"], "name": country.get("name") or country.get("nameKo")}

    # ---------- 표시용 조회: code -> name/flag 해석 ----------
    def get_travel_country_info(self, uid: str) -> Optional[Dict]:
        """
        홈 화면에서 표시할 사용자 여행국가 정보.
        - DB에서 code만 읽고
        - countries 컬렉션으로 표시용 데이터(nameKo/name/flag) 합성
        """
        user_doc = firestore_client.db.collection("users").document(uid).get()
        if not user_doc.exists:
            return None

        code = (user_doc.to_dict() or {}).get("currentCountry")
        if not code:
            return None

        c = self._get_country_by_code(code)
        if not c:
            return None

        return {
            "countryCode": c["code"],
            "countryName": c.get("nameKo") or c.get("name"),  # 한국어 우선 표시
            "flag": c.get("flag"),
        }

home_service = HomeService()
