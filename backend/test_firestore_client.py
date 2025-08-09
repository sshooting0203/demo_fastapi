#!/usr/bin/env python3
"""
Firestore 클라이언트 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.firestore_client import db, firestore_client

def test_firestore_client():
    """Firestore 클라이언트 테스트"""
    print("Firestore 클라이언트 테스트 시작")
    
    try:
        print("1. 클라이언트 연결 테스트...")
        client = firestore_client
        print(f"클라이언트 타입: {type(client)}")
        
        print("2. DB 인스턴스 테스트...")
        db_instance = db
        print(f"DB 타입: {type(db_instance)}")
        
        print("3. 간단한 쿼리 테스트...")
        countries_ref = db.collection('countries')
        docs = list(countries_ref.limit(1).stream())
        print(f"countries 컬렉션 조회 성공: {len(docs)}개 문서")
        
        if docs:
            doc_data = docs[0].to_dict()
            print(f"첫 번째 문서: {doc_data.get('nameKo', 'N/A')}")
        
        print("모든 테스트 통과")
        return True
        
    except Exception as e:
        print(f"테스트 실패: {e}")
        return False

if __name__ == "__main__":
    success = test_firestore_client()
    sys.exit(0 if success else 1)
