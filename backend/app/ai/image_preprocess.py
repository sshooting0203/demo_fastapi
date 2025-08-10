# image_preprocess.py
from io import BytesIO
import cv2
import numpy as np
from PIL import Image, ImageOps

#  EXIF 정보를 읽어서 이미지 자체를 올바른 방향으로 변환
def _read_with_orientation(img):
    img = ImageOps.exif_transpose(img)
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

# 4개의 점 정렬 
def _order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1); diff = np.diff(pts, axis=1)
    rect[0] = pts[np.argmin(s)]   # tl
    rect[2] = pts[np.argmax(s)]   # br
    rect[1] = pts[np.argmin(diff)]# tr
    rect[3] = pts[np.argmax(diff)]# bl
    return rect

# 실제로 계산한 점에 대해 변환 
def _four_point_transform(image, pts):
    rect = _order_points(pts)
    (tl, tr, br, bl) = rect

    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxW = int(max(widthA, widthB))

    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxH = int(max(heightA, heightB))

    dst = np.array([[0,0],[maxW-1,0],[maxW-1,maxH-1],[0,maxH-1]], dtype="float32")
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxW, maxH), flags=cv2.INTER_CUBIC)
    return warped

# 문서/메뉴판 외곽 4각형 추정 실패하면 None리턴 
def _detect_document_quad(img): 
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5,5), 0)
    edges = cv2.Canny(gray, 50, 150)
    edges = cv2.dilate(edges, np.ones((3,3), np.uint8), iterations=1)

    h_img, w_img = gray.shape[:2]
    img_area = w_img * h_img

    cnts, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:10]
    for c in cnts:
        area = cv2.contourArea(c)
        if area < 0.7 * img_area:  # 너무 작은건 무시
            continue
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            return approx.reshape(4, 2).astype("float32")
    return None

def resize_for_vision(img, target_long=2000):
    h, w = img.shape[:2]
    long = max(h, w)
    scale = target_long / long
    new_w, new_h = int(round(w*scale)), int(round(h*scale))
    interp = cv2.INTER_CUBIC if scale > 1 else cv2.INTER_AREA
    return cv2.resize(img, (new_w, new_h), interpolation=interp)

def preprocess_image(input_data, rectify=True):
    if isinstance(input_data, (bytes, bytearray)):
        pil = Image.open(BytesIO(input_data))
    else:
        pil = Image.open(str(input_data))

    src = _read_with_orientation(pil)
    quad = _detect_document_quad(src) if rectify else None
    if quad is not None:
        src = _four_point_transform(src, quad)
    src = resize_for_vision(src)
    return src

# =========Test Code=========
# disp = preprocess_image('./image.png')
# scale = 0.4  # 절반 크기
# small = cv2.resize(disp, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
# cv2.imshow("Preview", small)
# cv2.waitKey(0)
# cv2.destroyAllWindows()