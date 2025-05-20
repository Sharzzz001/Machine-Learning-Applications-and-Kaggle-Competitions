import fitz  # PyMuPDF
from PIL import Image
import cv2
import numpy as np

# --- Constants ---
PDF_PATH = "scanned.pdf"
PAGE_NUMBER = 0
ZOOM = 3  # High DPI: 3 = 216 DPI
DISPLAY_SCALE = 0.3  # Resize for screen preview

# --- Step 1: Load high-res image ---
doc = fitz.open(PDF_PATH)
page = doc.load_page(PAGE_NUMBER)
mat = fitz.Matrix(ZOOM, ZOOM)
pix = page.get_pixmap(matrix=mat)
image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

# Convert PIL to OpenCV
image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
height, width = image_cv.shape[:2]

# Resize image for display
display_img = cv2.resize(image_cv, (int(width * DISPLAY_SCALE), int(height * DISPLAY_SCALE)))

# --- Step 2: Interactive Crop Box Selection ---
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

# Setup window
cv2.namedWindow("Image", cv2.WINDOW_NORMAL)
cv2.setMouseCallback("Image", click_and_crop)
cv2.imshow("Image", display_img)
cv2.waitKey(0)
cv2.destroyAllWindows()
