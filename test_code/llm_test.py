import requests
import json

url = "http://127.0.0.1:8000/api/food/analyze"

payload = {
    "uid": "user_001",
    "source_language": "SP",
    "target_language": "KR",
    "food_name": "Chistorra",
}

headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, headers=headers, json=payload)

print("Status Code:", response.status_code)
try:
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
except json.JSONDecodeError:
    print(response.text)
