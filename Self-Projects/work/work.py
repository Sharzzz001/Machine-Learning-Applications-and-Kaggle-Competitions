import fitz  # PyMuPDF
import cv2
import numpy as np
import sys

def render_pdf_page(pdf_path, page_number, zoom=2.0):
    doc = fitz.open(pdf_path)
    if page_number < 0 or page_number >= len(doc):
        raise ValueError("Invalid page number.")

    page = doc[page_number]
    mat = fitz.Matrix(zoom, zoom)  # zoom to increase resolution
    pix = page.get_pixmap(matrix=mat)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:  # remove alpha if present
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return img

refPt = []
cropping = False

def click_and_crop(event, x, y, flags, param):
    global refPt, cropping, image

    if event == cv2.EVENT_LBUTTONDOWN:
        refPt = [(x, y)]
        cropping = True

    elif event == cv2.EVENT_LBUTTONUP:
        refPt.append((x, y))
        cropping = False
        cv2.rectangle(image, refPt[0], refPt[1], (0, 255, 0), 2)
        cv2.imshow("PDF Page", image)
        x1, y1 = refPt[0]
        x2, y2 = refPt[1]
        print(f"Crop box: ({x1}, {y1}, {x2}, {y2})")

def interactive_crop_from_pdf(pdf_path, page_number):
    global image
    image = render_pdf_page(pdf_path, page_number)
    clone = image.copy()

    cv2.namedWindow("PDF Page")
    cv2.setMouseCallback("PDF Page", click_and_crop)

    while True:
        cv2.imshow("PDF Page", image)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("r"):
            image = clone.copy()
        elif key == ord("q"):
            break

    cv2.destroyAllWindows()

# Example usage:
# interactive_crop_from_pdf("sample.pdf", 2)