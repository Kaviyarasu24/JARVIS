import cv2
import numpy as np
from PIL import Image #pillow package
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLES_DIR = os.path.join(BASE_DIR, 'samples')  # Path for samples already taken
TRAINER_DIR = os.path.join(BASE_DIR, 'trainer')
CASCADE_PATH = os.path.join(BASE_DIR, 'haarcascade_frontalface_default.xml')
CASCADE_FALLBACK = os.path.join(cv2.data.haarcascades, 'haarcascade_frontalface_default.xml')

# Check if samples directory exists and has images
if not os.path.exists(SAMPLES_DIR):
    print(f"Error: '{SAMPLES_DIR}' directory not found. Please run Sample generator.py first.")
    exit(1)

if len(os.listdir(SAMPLES_DIR)) == 0:
    print(f"Error: No face samples found in '{SAMPLES_DIR}' directory. Please run Sample generator.py first.")
    exit(1)

recognizer = cv2.face.LBPHFaceRecognizer_create() # Local Binary Patterns Histograms
detector_path = CASCADE_PATH if os.path.exists(CASCADE_PATH) else CASCADE_FALLBACK
detector = cv2.CascadeClassifier(detector_path)
if detector.empty():
    print(f"Error: Could not load Haar cascade from '{detector_path}'.")
    exit(1)
#Haar Cascade classifier is an effective object detection approach


def Images_And_Labels(path): # function to fetch the images and labels

    imagePaths = [
        os.path.join(path, f)
        for f in os.listdir(path)
        if os.path.isfile(os.path.join(path, f))
    ]
    faceSamples=[]
    ids = []

    for imagePath in imagePaths: # to iterate particular image path
        file_name = os.path.basename(imagePath)
        parts = file_name.split('.')
        if len(parts) < 4 or parts[0] != 'face' or not parts[1].isdigit():
            print(f"Skipping invalid sample name: {file_name}")
            continue

        gray_img = Image.open(imagePath).convert('L') # convert it to grayscale
        img_arr = np.array(gray_img,'uint8') #creating an array

        id = int(parts[1])
        faces = detector.detectMultiScale(img_arr)

        for (x,y,w,h) in faces:
            faceSamples.append(img_arr[y:y+h,x:x+w])
            ids.append(id)

    return faceSamples,ids

print ("Training faces. It will take a few seconds. Wait ...")

faces,ids = Images_And_Labels(SAMPLES_DIR)

if len(faces) == 0:
    print("Error: No faces detected in samples. Please ensure Sample generator.py saved valid face images.")
    exit(1)

recognizer.train(faces, np.array(ids))

# Create trainer directory if it doesn't exist
os.makedirs(TRAINER_DIR, exist_ok=True)

recognizer.write(os.path.join(TRAINER_DIR, 'trainer.yml'))  # Save the trained model as trainer.yml

print("Model trained successfully! Now you can run Face recognition.py")
