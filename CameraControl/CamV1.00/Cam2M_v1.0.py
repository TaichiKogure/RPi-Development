# save_media.py

import cv2
import os
import numpy as np
from datetime import datetime

# --- OUTPUT DIRECTORY ---
OUTPUT_DIR = "/home/koguretaichi/Documents/2MPcamera"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- CAMERA INITIALIZATION ---
cap = cv2.VideoCapture(0)  # 0 = default camera

# Set resolution
WIDTH = 1280
HEIGHT = 720
cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

# Set frame rate
FPS = 30.0
cap.set(cv2.CAP_PROP_FPS, FPS)

# Prepare video writer (MP4 format)
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
video_filename = os.path.join(
    OUTPUT_DIR, f"video_{WIDTH}x{HEIGHT}_{int(FPS)}fps.mp4"
)
writer = cv2.VideoWriter(video_filename, fourcc, FPS, (WIDTH, HEIGHT))

if not cap.isOpened():
    raise IOError("Cannot open camera")

print("Press 'q' key to exit")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Frame capture failed, stopping.")
        break

    # --- IMAGE ADJUSTMENTS ---
    # Adjust contrast and brightness
    alpha = 1.2  # contrast control (1.0 = no change)
    beta = 10    # brightness control (0?100)
    adjusted = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)

    # Convert to grayscale
    gray = cv2.cvtColor(adjusted, cv2.COLOR_BGR2GRAY)

    # Apply sharpening filter
    sharpen_kernel = np.array([
        [ 0, -1,  0],
        [-1,  5, -1],
        [ 0, -1,  0]
    ])
    sharpened = cv2.filter2D(gray, -1, sharpen_kernel)

    # Show on screen
    cv2.imshow('Live Capture (press q)', sharpened)

    # --- SAVE IMAGE ---
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    img_path = os.path.join(OUTPUT_DIR, f"image_{now_str}.png")
    cv2.imwrite(img_path, sharpened)

    # --- WRITE TO VIDEO ---
    writer.write(adjusted)  # use color frame for video

    # Handle quit key
    if cv2.waitKey(int(1000 / FPS)) & 0xFF == ord('q'):
        break

# --- CLEAN UP ---
cap.release()
writer.release()
cv2.destroyAllWindows()
print("Video saved to:", video_filename)