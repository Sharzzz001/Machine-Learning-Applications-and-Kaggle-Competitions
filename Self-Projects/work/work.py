import os
import pytesseract
from pdf2image import convert_from_path

# Optional: Specify path to tesseract executable if needed
# pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

# Define your rules here: {output_filename: (keyword, page_number)}
PDF_RENAME_RULES = {
    "AAF.pdf": ("account opening form", 1),
    "KYC.pdf": ("kyc documentation", 2),
    "POA.pdf": ("power of attorney", 1),
    "PAN.pdf": ("permanent account number", 1),
    # Add more rules here...
}

def extract_text_from_page(pdf_path, page_number):
    images = convert_from_path(pdf_path, first_page=page_number, last_page=page_number)
    if not images:
        return ""
    return pytesseract.image_to_string(images[0]).lower()

def determine_new_filename(pdf_path):
    for new_filename, (keyword, page_number) in PDF_RENAME_RULES.items():
        try:
            text = extract_text_from_page(pdf_path, page_number)
            if keyword.lower() in text:
                return new_filename
        except Exception as e:
            print(f"Error processing {pdf_path} on page {page_number}: {e}")
    return None  # If no match found

def process_pdf(pdf_path, output_dir):
    new_filename = determine_new_filename(pdf_path)
    if new_filename:
        new_path = os.path.join(output_dir, new_filename)
        os.rename(pdf_path, new_path)
        print(f"Renamed '{pdf_path}' → '{new_path}'")
    else:
        print(f"No match found for '{pdf_path}'")

# Run this on a folder
def process_all_pdfs(folder_path):
    for file in os.listdir(folder_path):
        if file.lower().endswith(".pdf"):
            process_pdf(os.path.join(folder_path, file), folder_path)

# Example usage
if __name__ == "__main__":
    input_folder = "your/folder/with/pdfs"
    process_all_pdfs(input_folder)
