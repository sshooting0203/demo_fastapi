# Firestore TTL 설정 가이드

## TTL (Time To Live) 설정

Firestore 콘솔에서 다음 컬렉션에 TTL을 설정:

### 검색 결과 (search_results)
- **TTL 기간**: 7일
- **설정 방법**:
  1. Firestore 콘솔 → 데이터 → search_results 컬렉션
  2. TTL 탭 → TTL 활성화
  3. 필드: `timestamp`
  4. 기간: 7일

## 보안 규칙 배포

`firestore.rules` 파일을 Firestore에 배포:

```bash
firebase deploy --only firestore:rules
```

## 주의사항

- TTL은 Firestore에서 자동으로 처리
- 코드에서 TTL 필드를 설정할 필요가 없음
- TTL 설정 후 즉시 적용되지 않을 수 있음 (최대 24시간 소요)
-> 이건 나중에 설정(시간 나면)