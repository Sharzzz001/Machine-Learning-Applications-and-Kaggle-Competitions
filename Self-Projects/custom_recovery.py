import os
import cv2
import shutil
from PIL import Image
from PIL.ExifTags import TAGS

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Define paths to model files
model_path = "res10_300x300_ssd_iter_140000.caffemodel"
config_path = "deploy.prototxt"

# Load the DNN model
net = cv2.dnn.readNetFromCaffe(config_path, model_path)

# Input and output directories
source_directory = "D:\Sharan\Final HDD\\rejected"
accepted_directory = "D:\Sharan\Final HDD\\accepted"
rejected_directory = "D:\Sharan\Final HDD\\reject_2"

# Create the accepted and rejected folders if they don't exist
os.makedirs(accepted_directory, exist_ok=True)
os.makedirs(rejected_directory, exist_ok=True)

def has_exif_date_taken(file_path):
    """Check if the image has EXIF 'Date Taken' metadata."""
    try:
        image = Image.open(file_path)
        exif_data = image._getexif()  # Get EXIF metadata
        if not exif_data:
            return False
        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, tag_id)
            if tag_name == "DateTimeOriginal":  # EXIF "Date Taken"
                return True
    except Exception as e:
        print(f"Error reading EXIF data for {file_path}: {str(e)}")
    return False

def filter_images():
    for filename in os.listdir(source_directory):
        file_path = os.path.join(source_directory, filename)
        
        # Skip non-image files
        if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp')):
            continue
        
        try:
            # Check if EXIF 'Date Taken' is present
            if has_exif_date_taken(file_path):
                print(f"Accepted {filename}: EXIF 'Date Taken' present")
                shutil.move(file_path, os.path.join(accepted_directory, filename))
                continue
            
            # Check file size
            file_size_kb = os.path.getsize(file_path) / 1024  # Convert to KB
            if file_size_kb < 50:
                print(f"Rejected {filename}: File size is less than 50KB")
                shutil.move(file_path, os.path.join(rejected_directory, filename))
                continue
            
            # Load the image
            image = cv2.imread(file_path)
            if image is None:
                print(f"Rejected {filename}: Unable to read image")
                shutil.move(file_path, os.path.join(rejected_directory, filename))
                continue
            
            # Get image dimensions
            (h, w) = image.shape[:2]
            if h < 200 or w < 200:
                print(f"Rejected {filename}: Image dimensions are less than 200px")
                shutil.move(file_path, os.path.join(rejected_directory, filename))
                continue
            
            # Preprocess the image for the model
            blob = cv2.dnn.blobFromImage(image, 1.0, (300, 300), (104.0, 177.0, 123.0))
            net.setInput(blob)
            detections = net.forward()
            
            # Check for confidence score
            max_confidence = 0
            for i in range(detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                max_confidence = max(max_confidence, confidence)
            
            if max_confidence >= 0.7:
                print(f"Accepted {filename}: Confidence {max_confidence:.2f}")
                shutil.move(file_path, os.path.join(accepted_directory, filename))
            else:
                print(f"Rejected {filename}: Confidence {max_confidence:.2f}")
                shutil.move(file_path, os.path.join(rejected_directory, filename))
        
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            shutil.move(file_path, os.path.join(rejected_directory, filename))

# Run the filtering
filter_images()