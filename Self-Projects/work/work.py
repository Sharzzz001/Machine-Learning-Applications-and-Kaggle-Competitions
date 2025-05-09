import os
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

# Define rules: {filename: (keyword, page_number)}
PDF_RENAME_RULES = {
    "AAF.pdf": ("account opening form", 0),  # 0-based index
    "KYC.pdf": ("kyc documentation", 1),
    "POA.pdf": ("power of attorney", 0),
    # Add more rules as needed
}

def extract_text_from_page(pdf_path, page_number):
    with fitz.open(pdf_path) as doc:
        if page_number >= len(doc):
            return ""
        page = doc.load_page(page_number)
        pix = page.get_pixmap(dpi=300)
        img_bytes = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_bytes))
        text = pytesseract.image_to_string(image).lower()
        return text

def determine_new_filename(pdf_path):
    for new_filename, (keyword, page_num) in PDF_RENAME_RULES.items():
        try:
            text = extract_text_from_page(pdf_path, page_num)
            if keyword.lower() in text:
                return new_filename
        except Exception as e:
            print(f"Error reading {pdf_path} page {page_num + 1}: {e}")
    return None

def process_pdf(pdf_path, output_dir):
    new_filename = determine_new_filename(pdf_path)
    if new_filename:
        new_path = os.path.join(output_dir, new_filename)
        os.rename(pdf_path, new_path)
        print(f"Renamed: {os.path.basename(pdf_path)} → {new_filename}")
    else:
        print(f"No match for {os.path.basename(pdf_path)}")

def process_all_pdfs(folder_path):
    for file in os.listdir(folder_path):
        if file.lower().endswith(".pdf"):
            process_pdf(os.path.join(folder_path, file), folder_path)

# Example usage
if __name__ == "__main__":
    input_folder = "your/folder/with/pdfs"
    process_all_pdfs(input_folder)
