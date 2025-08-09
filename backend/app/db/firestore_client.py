import os
import json
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from typing import Optional

load_dotenv()

class FirestoreClient:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirestoreClient, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialize_firebase()
            self._initialized = True
    
    def _initialize_firebase(self):
        try:
            if not firebase_admin._apps:
                firebase_credentials = json.loads(os.getenv("FIREBASE_CREDENTIALS"))
                cred = credentials.Certificate(firebase_credentials)
                firebase_admin.initialize_app(cred)
                print("Firebase 초기화 완료")
            else:
                print("Firebase 이미 초기화됨")
        except Exception as e:
            print(f"Firebase 초기화 실패: {e}")
            raise
    
    @property
    def db(self):
        return firestore.client()
    
    def get_collection(self, collection_name: str):
        return self.db.collection(collection_name)
    
    def get_document(self, collection_name: str, doc_id: str):
        return self.db.collection(collection_name).document(doc_id)
    
    def get_subcollection(self, parent_ref, subcollection_name: str):
        return parent_ref.collection(subcollection_name)

# 싱글 인스턴스 생성
firestore_client = FirestoreClient()
db = firestore_client.db
