import cv2

# Load your image
image = cv2.imread("your_image.jpg")
clone = image.copy()

# Global variables for cropping
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

        # Draw rectangle
        cv2.rectangle(image, refPt[0], refPt[1], (0, 255, 0), 2)
        cv2.imshow("image", image)

        x1, y1 = refPt[0]
        x2, y2 = refPt[1]
        print(f"Crop box: ({x1}, {y1}, {x2}, {y2})")

# Set up the window and mouse callback
cv2.namedWindow("image")
cv2.setMouseCallback("image", click_and_crop)

while True:
    cv2.imshow("image", image)
    key = cv2.waitKey(1) & 0xFF

    # Press 'r' to reset
    if key == ord("r"):
        image = clone.copy()

    # Press 'q' to quit
    elif key == ord("q"):
        break

cv2.destroyAllWindows()