import fitz  # PyMuPDF
import pytesseract
from PIL import Image

doc = fitz.open("statement.pdf")

for i, page in enumerate(doc, start=1):
    # First try to extract text directly
    text = page.get_text("text")
    if text.strip():
        print(f"--- Page {i} (text extract) ---")
        print(text[:400])
    else:
        # If no text, fall back to OCR
        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        text = pytesseract.image_to_string(img, lang="eng+ara")
        print(f"--- Page {i} (OCR extract) ---")
        print(text[:400])