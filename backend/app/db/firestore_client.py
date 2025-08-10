# backend/app/db/firestore_client.py
import os
import json
import firebase_admin
from firebase_admin import credentials as fb_credentials
from google.oauth2 import service_account
from google.cloud import firestore as gcf

class FirestoreClient:
    """
    실 Firestore 전용 클라이언트.
    - 에뮬레이터 관련 로직 제거
    - FIREBASE_CREDENTIALS (JSON 문자열 또는 파일 경로)만으로
      firebase_admin + google.cloud Client 모두 초기화
    """

    def __init__(self) -> None:
        self._db = None
        self._initialized = False
        self._project_id = os.getenv("FIREBASE_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or None
        self._gcp_credentials = None

    def _load_service_account(self):
        """FIREBASE_CREDENTIALS에서 서비스 계정 로드 (문자열/경로 모두 지원)."""
        cred_env = os.getenv("FIREBASE_CREDENTIALS", "").strip()
        if not cred_env:
            raise RuntimeError("FIREBASE_CREDENTIALS 환경변수가 없습니다. 서비스 계정 JSON(문자열 또는 파일 경로)을 설정하세요.")

        # JSON 문자열인지 파일 경로인지 판별
        if cred_env.startswith("{"):
            info = json.loads(cred_env)
            fb_cred = fb_credentials.Certificate(info)
            gcp_cred = service_account.Credentials.from_service_account_info(info)
            project_id = info.get("project_id")
        else:
            if not os.path.exists(cred_env):
                raise FileNotFoundError(f"FIREBASE_CREDENTIALS 파일을 찾을 수 없습니다: {cred_env}")
            fb_cred = fb_credentials.Certificate(cred_env)
            gcp_cred = service_account.Credentials.from_service_account_file(cred_env)
            # 파일에도 project_id가 들어있음
            with open(cred_env, "r", encoding="utf-8") as f:
                project_id = json.load(f).get("project_id")

        return fb_cred, gcp_cred, project_id

    def _initialize(self):
        if self._initialized:
            return
        fb_cred, gcp_cred, sa_project_id = self._load_service_account()

        # project_id 우선순위: .env(FIREBASE_PROJECT_ID/GOOGLE_CLOUD_PROJECT) > 서비스계정의 project_id
        if not self._project_id:
            self._project_id = sa_project_id

        if not self._project_id:
            raise RuntimeError("프로젝트 ID를 결정할 수 없습니다. FIREBASE_PROJECT_ID(또는 GOOGLE_CLOUD_PROJECT)를 설정하거나 서비스 계정에 project_id가 포함돼야 합니다.")

        # Firebase Admin 초기화
        if not firebase_admin._apps:
            firebase_admin.initialize_app(fb_cred, {"projectId": self._project_id})
            print("Firebase 초기화 성공(실 Firestore)")

        # google.cloud용 자격증명 확보
        self._gcp_credentials = gcp_cred
        self._initialized = True

    @property
    def db(self):
        if not self._initialized:
            self._initialize()
        if not self._db:
            # google.cloud Firestore 클라이언트에 같은 자격증명을 명시적으로 전달
            self._db = gcf.Client(project=self._project_id, credentials=self._gcp_credentials)
        return self._db

    def get_collection(self, collection_name: str):
        return self.db.collection(collection_name)

    def get_document(self, collection_name: str, doc_id: str):
        return self.db.collection(collection_name).document(doc_id)

# 싱글톤 인스턴스
firestore_client = FirestoreClient()
