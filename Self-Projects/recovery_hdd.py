import os
import shutil
import cv2

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Define source and destination directories
source_dir = "C:\Sharan\\recovery-photorec"
destination_dir = "D:\Sharan\Recovery Images HDD\Filter"

# Supported image file extensions
image_extensions = ['.jpg','.JPG', '.jpeg','.JPEG', '.png','.PNG', '.bmp', '.tiff']

# Function to check if a file is an image
def is_image_file(file_path):
    return any(file_path.lower().endswith(ext) for ext in image_extensions)

# Function to detect humans in an image
def detect_humans(image_path):
    # Load the pre-trained YOLO face detection model
    net = cv2.dnn.readNetFromCaffe(
        'deploy.prototxt',  # Download: https://github.com/opencv/opencv/tree/master/samples/dnn/face_detector
        'res10_300x300_ssd_iter_140000.caffemodel'
    )
    
    # Read the image
    image = cv2.imread(image_path)
    if image is None:
        return False  # Skip invalid files

    (h, w) = image.shape[:2]
    blob = cv2.dnn.blobFromImage(image, 1.0, (300, 300), (104.0, 177.0, 123.0))
    net.setInput(blob)
    detections = net.forward()

    # Check for human-like objects
    for i in range(0, detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > 0.5:  # Confidence threshold
            # Human detected
            return True
    return False

# Process images
for root, _, files in os.walk(source_dir):
    for file in files:
        file_path = os.path.join(root, file)

        if is_image_file(file_path):
            print(f"Processing: {file_path}")
            try:
                if detect_humans(file_path):
                    print(f"Human detected in: {file_path}")
                    dest_path = os.path.join(destination_dir, os.path.basename(file_path))  # Dump directly into destination
                    shutil.copy2(file_path, dest_path)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")