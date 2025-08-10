import firebase_admin
from firebase_admin import credentials, firestore
from typing import Optional, Dict, Any, List
import os
import json
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class FirestoreClient:
    def __init__(self):
        self._db = None
        self._initialized = False
    
    def _initialize_firebase(self):
        """Firebase 초기화 (필요할 때만)"""
        if not self._initialized:
            try:
                if not firebase_admin._apps:
                    # FIREBASE_CREDENTIALS 환경변수에서 JSON 읽기
                    firebase_creds_json = os.getenv('FIREBASE_CREDENTIALS')
                    
                    if firebase_creds_json:
                        try:
                            # JSON 문자열을 파싱
                            creds_dict = json.loads(firebase_creds_json)
                            cred = credentials.Certificate(creds_dict)
                            firebase_admin.initialize_app(cred)
                            self._initialized = True
                            print("Firebase 초기화 성공: FIREBASE_CREDENTIALS 환경변수 사용")
                        except json.JSONDecodeError as e:
                            print(f"FIREBASE_CREDENTIALS JSON 파싱 실패: {e}")
                            return
                        except Exception as e:
                            print(f"Firebase 인증서 생성 실패: {e}")
                            return
                    else:
                        # 기존 파일 경로 방식도 지원 (하위 호환성)
                        service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', 'path/to/serviceAccountKey.json')
                        
                        if os.path.exists(service_account_path):
                            cred = credentials.Certificate(service_account_path)
                            firebase_admin.initialize_app(cred)
                            self._initialized = True
                            print(f"Firebase 초기화 성공: 파일 경로 사용 - {service_account_path}")
                        else:
                            print(f"경고: Firebase 인증 정보를 찾을 수 없습니다.")
                            print("FIREBASE_CREDENTIALS 환경변수 또는 FIREBASE_SERVICE_ACCOUNT_PATH 파일을 확인해주세요.")
                            return
                else:
                    self._initialized = True
            except Exception as e:
                print(f"Firebase 초기화 실패: {e}")
                print("Firebase 기능을 사용할 수 없습니다.")
    
    @property
    def db(self):
        """Firestore 데이터베이스 클라이언트 반환"""
        if not self._initialized:
            self._initialize_firebase()
        
        if self._initialized:
            if not self._db:
                self._db = firestore.client()
            return self._db
        else:
            raise Exception("Firebase가 초기화되지 않았습니다. FIREBASE_CREDENTIALS 환경변수를 확인해주세요.")
    
    def get_collection(self, collection_name: str):
        """컬렉션 참조 반환"""
        return self.db.collection(collection_name)
    
    def get_document(self, collection_name: str, doc_id: str):
        """문서 참조 반환"""
        return self.db.collection(collection_name).document(doc_id)

# 전역 인스턴스
firestore_client = FirestoreClient()
