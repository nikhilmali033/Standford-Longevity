import cv2
import numpy as np
import pytesseract
from PIL import Image

def main():
    # Create a blank image (canvas)
    canvas = np.ones((480, 640, 3), dtype=np.uint8) * 255
    cv2.namedWindow("Canvas")

    # Variables for drawing
    drawing = False
    last_x, last_y = -1, -1

    def draw(event, x, y, flags, param):
        nonlocal drawing, last_x, last_y

        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            last_x, last_y = x, y
        elif event == cv2.EVENT_MOUSEMOVE:
            if drawing:
                cv2.line(canvas, (last_x, last_y), (x, y), (0, 0, 0), 2)
                last_x, last_y = x, y
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False

    cv2.setMouseCallback("Canvas", draw)

    while True:
        cv2.imshow("Canvas", canvas)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break
        elif key == ord('c'):
            canvas = np.ones((480, 640, 3), dtype=np.uint8) * 255
        elif key == ord('r'):
            # Convert the image to grayscale
            gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
            
            # Use Tesseract to do OCR on the image
            text = pytesseract.image_to_string(Image.fromarray(gray))
            
            print("Recognized text:")
            print(text)

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()