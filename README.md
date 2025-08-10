**검색 1건이 발생했음을 시스템의 ‘사실’로 기록하는 API(선택)**

@router.post("/search")

async def search(req: SearchRequest, uid: Optional\[str] = Depends(auth\_optional)):

&nbsp;   1. country\_rankings.{C}.foods.{foodId} searchCount += 1, lastSearched

&nbsp;   2. search\_logs TTL write

&nbsp;   3. popular\_foods 상태 판정 → hit/queued/updated

&nbsp;   return {...}

-SearchRequest

{

&nbsp; "country": "JP",

&nbsp; "originalText": "とんかつ",

&nbsp; "translatedText": "돈카츠",

&nbsp; "foodId": "JP\_tonkatsu",          // 없으면 서버가 생성 규칙으로 부여(슬러그화)

}

-Response

{

&nbsp; "foodId": "JP\_tonkatsu",

&nbsp; "enrichment": "hit|queued|updated",   // popular\_foods 상태

&nbsp; "popularFood": { /\* 있을 때만 최소 필드 포함 \*/ }

}



**사용자가 선택한 요리 저장하는 API**

@router.post("/users/me/saved-foods", status\_code=201)

async def save\_food(req: SaveFoodRequest, uid: str = Depends(auth\_required)):

&nbsp;   1. users/{uid}/saved\_foods/{foodId} upsert

&nbsp;   2. country\_rankings/{C}/foods/{foodId}.saveCount += 1, lastSaved = now()

&nbsp;   3. popular\_foods 비어있으면 보강 큐잉

&nbsp;   return {...}

-SaveFoodRequest

{

&nbsp; "country": "ES",

&nbsp; "foodName": "Paella",

&nbsp; "translatedText": "빠에야",

&nbsp; "userImageUrl": "https://...",

&nbsp; "summaryShort": "스페인 쌀요리",

&nbsp; "allergens": \["SHELLFISH"],

&nbsp; "restaurantName": "Bar La Pepa",

&nbsp; "review": "정말 맛있음",        // optional

&nbsp; "rating": 4.5                  // optional

}



**사용자가 선택한 요리 삭제하는 API**

@router.delete("/users/me/saved-foods/{foodId}", status\_code=204)

async def delete\_saved(foodId: str, uid: str = Depends(auth\_required)):

&nbsp;   1. 서브컬렉션 삭제(카운트 다운X)

&nbsp;   return Response(status\_code=204)



사용자가 선택한 요리 조회하는 API

@router.get("/users/me/saved-foods")

async def list\_saved(...): ...



**인기 랭킹 조회하는 API**

@router.get("/countries/{country}/top", response\_model=CountryTopResponse)

async def get\_top(country: str): ...

&nbsp;   1. country\_rankings/{C}/top 문서 read

-Response

{

&nbsp; "country": "JP",

&nbsp; "topFoods": \[

&nbsp;   { "foodId": "JP\_tonkatsu", "foodName": "Tonkatsu", "imageUrl": "...", "searchCount": 123, "saveCount": 45 },

&nbsp;   { "foodId": "JP\_ramen", ... },

&nbsp;   { "foodId": "JP\_sushi", ... }

&nbsp; ],

&nbsp; "snapshotAt": "2025-08-09T12:00:00Z"

}



