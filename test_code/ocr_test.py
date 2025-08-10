import requests

BASE = "http://127.0.0.1:8000"

def test_with_file():
    path = "C:\\Users\\sshl5\\IdeaProjects\\unithon-backend\\backend\\app\\ai\\test_img\\image6.png"

    files = {
        "file": (path, open(path, "rb"), "image/jpeg")
    }
    data = {"target_language": "EN"}
    r = requests.post(f"{BASE}/api/food/ocr-translate", data=data, files=files, timeout=60)
    r.raise_for_status()
    print("status:", r.status_code)
    print("json:", r.json())

def test_with_image_url():
    data = {
        "target_language": "EN",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/6/6b/Menu.jpg"
    }
    r = requests.post(f"{BASE}/ocr-translate", data=data, timeout=60)
    r.raise_for_status()
    print("status:", r.status_code)
    print("json:", r.json())

if __name__ == "__main__":
    test_with_file()
    # test_with_image_url()
