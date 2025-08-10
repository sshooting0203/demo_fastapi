# backend/app/db/firestore_client.py
import os
import json
import firebase_admin
from firebase_admin import credentials as fb_credentials
from google.oauth2 import service_account
from google.cloud import firestore as gcf
import logging

logger = logging.getLogger(__name__)

class FirestoreClient:
    """
    Google Cloud Firestore 클라이언트
    
    주요 기능:
    - Firebase Admin SDK 초기화
    - Google Cloud Firestore 클라이언트 제공
    - 서비스 계정 인증 정보 관리
    - 싱글톤 패턴으로 인스턴스 관리
    """

    def __init__(self) -> None:
        """Firestore 클라이언트 초기화"""
        self._db = None
        self._initialized = False
        self._project_id = os.getenv("FIREBASE_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or None
        # 테스트하느라 이것저것 섞임 -> 나중에 구글 클라우드 빼기
        self._gcp_credentials = None

    def _load_service_account(self):
        """
        FIREBASE_CREDENTIALS에서 firebase 웹서비스 키 가져옴
        
        Returns:
            tuple: (Firebase 자격증명, Google Cloud 자격증명, 프로젝트 ID)
            
        Raises:
            RuntimeError: 환경변수가 설정되지 않은 경우
            FileNotFoundError: 파일 경로가 유효하지 않은 경우
        """
        cred_env = os.getenv("FIREBASE_CREDENTIALS", "").strip()
        if not cred_env:
            raise RuntimeError("FIREBASE_CREDENTIALS 환경변수가 없습니다. 서비스 계정 JSON(문자열 또는 파일 경로)을 설정하세요.")

        # JSON 문자열인지 파일 경로인지 판별
        if cred_env.startswith("{"):
            # JSON 문자열로 직접 제공된 경우
            info = json.loads(cred_env)
            fb_cred = fb_credentials.Certificate(info)
            gcp_cred = service_account.Credentials.from_service_account_info(info)
            project_id = info.get("project_id")
        else:
            # 파일 경로로 제공된 경우
            if not os.path.exists(cred_env):
                raise FileNotFoundError(f"FIREBASE_CREDENTIALS 파일을 찾을 수 없습니다: {cred_env}")
            fb_cred = fb_credentials.Certificate(cred_env)
            gcp_cred = service_account.Credentials.from_service_account_file(cred_env)
            # 파일에서 프로젝트 ID 읽기
            with open(cred_env, "r", encoding="utf-8") as f:
                project_id = json.load(f).get("project_id")

        return fb_cred, gcp_cred, project_id

    def _initialize(self):
        """Firebase Admin SDK 및 Firestore 클라이언트 초기화"""
        if self._initialized:
            return
            
        fb_cred, gcp_cred, sa_project_id = self._load_service_account()

        # 프로젝트 ID 우선순위: .env > 서비스계정의 project_id
        if not self._project_id:
            self._project_id = sa_project_id

        if not self._project_id:
            raise RuntimeError("프로젝트 ID를 결정할 수 없습니다. FIREBASE_PROJECT_ID(또는 GOOGLE_CLOUD_PROJECT)를 설정하거나 서비스 계정에 project_id가 포함돼야 합니다.")

        # Firebase Admin 초기화 (중복 초기화 방지)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(fb_cred, {"projectId": self._project_id})
            logger.info("Firebase Admin SDK 초기화 완료")

        # Google Cloud 자격증명 저장
        self._gcp_credentials = gcp_cred
        self._initialized = True

    @property
    def db(self):
        """
        Firestore 데이터베이스 클라이언트 반환
        
        Returns:
            google.cloud.firestore.Client: Firestore 클라이언트 인스턴스
        """
        if not self._initialized:
            self._initialize()
        if not self._db:
            # Google Cloud Firestore 클라이언트 생성
            self._db = gcf.Client(project=self._project_id, credentials=self._gcp_credentials)
        return self._db

    def get_collection(self, collection_name: str):
        """
        특정 컬렉션 참조 반환
        
        Args:
            collection_name (str): 컬렉션 이름
            
        Returns:
            google.cloud.firestore.CollectionReference: 컬렉션 참조
        """
        return self.db.collection(collection_name)

    def get_document(self, collection_name: str, doc_id: str):
        """
        특정 문서 참조 반환
        
        Args:
            collection_name (str): 컬렉션 이름
            doc_id (str): 문서 ID
            
        Returns:
            google.cloud.firestore.DocumentReference: 문서 참조
        """
        return self.db.collection(collection_name).document(doc_id)

# 싱글톤 인스턴스
firestore_client = FirestoreClient()
