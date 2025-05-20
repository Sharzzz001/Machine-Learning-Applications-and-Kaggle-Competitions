import fitz  # PyMuPDF
from PIL import Image
import easyocr

def extract_text_from_pdf(pdf_path, page_num=0, crop_coords=(100, 300, 100, 300)):
    """
    Extract handwritten/printed text from a cropped area of a PDF page.

    :param pdf_path: Path to the PDF file.
    :param page_num: Page number (0-indexed).
    :param crop_coords: Tuple of (left, right, top, bottom) pixels for cropping.
    :return: OCR extracted text.
    """
    # Open PDF and select page
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_num)

    # Render high-resolution image (e.g. 3x zoom ~ 216 DPI)
    zoom = 3
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)

    # Convert to PIL Image
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    # Unpack cropping coordinates
    left, right, top, bottom = crop_coords

    # Crop the image
    cropped_img = img.crop((left, top, right, bottom))

    # OCR using EasyOCR
    reader = easyocr.Reader(['en'], gpu=False)
    results = reader.readtext(np.array(cropped_img), detail=0)  # detail=0 returns only text

    # Print the recognized text
    print("OCR Output:")
    for line in results:
        print(line)

    return results

# Example usage
if __name__ == "__main__":
    pdf_path = "your_scanned_doc.pdf"
    page_num = 0  # First page
    crop_coords = (100, 600, 150, 300)  # (left, right, top, bottom)

    extract_text_from_pdf(pdf_path, page_num, crop_coords)
