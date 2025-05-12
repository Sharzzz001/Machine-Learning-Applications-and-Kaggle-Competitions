import fitz  # PyMuPDF
from PIL import Image
import numpy as np
import cv2

def get_crop_box_from_pdf(pdf_path, page_number):
    # Load PDF and page
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_number)  # 0-indexed
    pix = page.get_pixmap(dpi=150)  # Higher DPI = better resolution
    img_pil = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    # Convert PIL image to OpenCV
    img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    clone = img_cv.copy()
    refPt = []
    cropping = [False]  # use list for mutability in nested func

    def click_and_crop(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            refPt.clear()
            refPt.append((x, y))
            cropping[0] = True

        elif event == cv2.EVENT_LBUTTONUP:
            refPt.append((x, y))
            cropping[0] = False
            cv2.rectangle(img_cv, refPt[0], refPt[1], (0, 255, 0), 2)
            cv2.imshow("Select Region", img_cv)

    cv2.namedWindow("Select Region")
    cv2.setMouseCallback("Select Region", click_and_crop)

    while True:
        cv2.imshow("Select Region", img_cv)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("c") and len(refPt) == 2:
            break
        elif key == 27:  # ESC to exit
            refPt = []
            break

    cv2.destroyAllWindows()

    if len(refPt) == 2:
        (x1, y1), (x2, y2) = refPt
        left, top, right, bottom = min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)
        cropped = img_pil.crop((left, top, right, bottom))
        cropped.show()
        print(f"Crop box for PIL.crop(): ({left}, {top}, {right}, {bottom})")
        return (left, top, right, bottom)

    else:
        print("No region selected.")
        return None

# === Usage ===
pdf_path = "your_file.pdf"
page_number = 0  # Zero-based index (0 = first page)
get_crop_box_from_pdf(pdf_path, page_number)