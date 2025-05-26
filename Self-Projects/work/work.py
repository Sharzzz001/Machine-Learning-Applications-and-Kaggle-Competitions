import fitz  # PyMuPDF
from PIL import Image
import cv2
import numpy as np

# --- Constants ---
PDF_PATH = "scanned.pdf"
PAGE_NUMBER = 0
ZOOM = 3  # High DPI: 3 = 216 DPI
DISPLAY_SCALE = 0.3  # Resize for screen preview

# --- Step 0: Deskewing Function ---
def deskew_image(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.bitwise_not(gray)

    thresh = cv2.threshold(gray, 0, 255,
                           cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    coords = np.column_stack(np.where(thresh > 0))
    angle = cv2.minAreaRect(coords)[-1]

    # Correct the angle
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    # Rotate the image to deskew it
    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)

    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    deskewed = cv2.warpAffine(img, M, (w, h),
                              flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return deskewed

# --- Step 1: Load high-res image from PDF ---
doc = fitz.open(PDF_PATH)
page = doc.load_page(PAGE_NUMBER)
mat = fitz.Matrix(ZOOM, ZOOM)
pix = page.get_pixmap(matrix=mat)
image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

# Convert PIL to OpenCV
image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

# --- Step 2: Deskew image before anything else ---
image_cv = deskew_image(image_cv)

# Resize image for display
height, width = image_cv.shape[:2]
display_img = cv2.resize(image_cv, (int(width * DISPLAY_SCALE), int(height * DISPLAY_SCALE)))

# --- Step 3: Interactive Crop Box Selection ---
refPt = []
cropping = False

def click_and_crop(event, x, y, flags, param):
    global refPt, cropping

    if event == cv2.EVENT_LBUTTONDOWN:
        refPt = [(x, y)]
        cropping = True

    elif event == cv2.EVENT_LBUTTONUP:
        refPt.append((x, y))
        cropping = False

        cv2.rectangle(display_img, refPt[0], refPt[1], (0, 255, 0), 2)
        cv2.imshow("Image", display_img)

        # Scale back to original DPI
        x1, y1 = int(refPt[0][0] / DISPLAY_SCALE), int(refPt[0][1] / DISPLAY_SCALE)
        x2, y2 = int(refPt[1][0] / DISPLAY_SCALE), int(refPt[1][1] / DISPLAY_SCALE)
        crop_box = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        print("Crop box for high-res image:", crop_box)

# --- Step 4: Setup display window ---
cv2.namedWindow("Image", cv2.WINDOW_NORMAL)
cv2.setMouseCallback("Image", click_and_crop)
cv2.imshow("Image", display_img)
cv2.waitKey(0)
cv2.destroyAllWindows()
