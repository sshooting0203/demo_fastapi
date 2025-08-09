import os, json
from dotenv import load_dotenv
from google.cloud import vision
from google.oauth2 import service_account
import time 

load_dotenv()
info = json.loads(os.getenv("GOOGLE_OCR_CREDENTIALS")) # 1.394 초
creds = service_account.Credentials.from_service_account_info(info)
client = vision.ImageAnnotatorClient(credentials=creds)
path = './image.png'
def detect_text(path, client):
    with open(path, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    start_time = time.time()
    response = client.text_detection(image=image, image_context={"language_hints": ["ko"]})
    elapsed_time = time.time() - start_time
    print(f"Vision API 요청 시간: {elapsed_time:.3f} 초")

    texts = response.text_annotations

    print("Texts:")
    langs = []
    fta = response.full_text_annotation
    if fta and fta.pages:
        for page in fta.pages:
            if page.property and page.property.detected_languages:
                for l in page.property.detected_languages:
                    langs.append((l.language_code, getattr(l, "confidence", 0.0)))

    print('Lang : ', langs)

    for text in texts:
        print(f'\n"{text.description}"')

        vertices = [
            f"({vertex.x},{vertex.y})" for vertex in text.bounding_poly.vertices
        ]

        print("bounds: {}".format(",".join(vertices)))

    if response.full_text_annotation.pages:
        for page in response.full_text_annotation.pages:
            for block in page.blocks:
                if block.property.detected_languages:
                    for lang in block.property.detected_languages:
                        print(f"Detected language: {lang.language_code}, Confidence: {lang.confidence}")

    if response.error.message:
        raise Exception(
            "{}\nFor more info on error messages, check: "
            "https://cloud.google.com/apis/design/errors".format(response.error.message)
        )
detect_text(path, client)