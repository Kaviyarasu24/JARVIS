import cv2
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRAINER_PATH = os.path.join(BASE_DIR, 'trainer', 'trainer.yml')
CASCADE_PATH = os.path.join(BASE_DIR, 'haarcascade_frontalface_default.xml')
CASCADE_FALLBACK = os.path.join(cv2.data.haarcascades, 'haarcascade_frontalface_default.xml')

recognizer = cv2.face.LBPHFaceRecognizer_create() # Local Binary Patterns Histograms
if not os.path.exists(TRAINER_PATH):
    print("Error: Trainer model not found. Run Model Trainer.py first.")
    raise SystemExit(1)

recognizer.read(TRAINER_PATH)   #load trained model
cascade_path = CASCADE_PATH if os.path.exists(CASCADE_PATH) else CASCADE_FALLBACK
faceCascade = cv2.CascadeClassifier(cascade_path) #initializing haar cascade for object detection approach
if faceCascade.empty():
    print(f"Error: Could not load Haar cascade from '{cascade_path}'.")
    raise SystemExit(1)

font = cv2.FONT_HERSHEY_SIMPLEX #denotes the font type

# ID to name mapping - add your trained user IDs here
names = {
    7: 'User 07',      # User ID 7 (update with your name)
}


cam = cv2.VideoCapture(0, cv2.CAP_DSHOW) #cv2.CAP_DSHOW to remove warning
cam.set(3, 640) # set video FrameWidht
cam.set(4, 480) # set video FrameHeight

# Define min window size to be recognized as a face
minW = 0.1*cam.get(3)
minH = 0.1*cam.get(4)

while True:

    ret, img =cam.read() #read the frames using the above created object

    converted_image = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)  #The function converts an input image from one color space to another

    faces = faceCascade.detectMultiScale( 
        converted_image,
        scaleFactor = 1.2,
        minNeighbors = 5,
        minSize = (int(minW), int(minH)),
       )

    for(x,y,w,h) in faces:

        cv2.rectangle(img, (x,y), (x+w,y+h), (0,255,0), 2) #used to draw a rectangle on any image

        id, accuracy = recognizer.predict(converted_image[y:y+h,x:x+w]) #to predict on every single image

        # Check if accuracy is less than 100 ==> "0" is perfect match 
        if (accuracy < 100):
            person_name = names.get(id, f"User {id}")
            confidence = "  {0}%".format(round(100 - accuracy))
        else:
            person_name = "unknown"
            confidence = "  {0}%".format(round(100 - accuracy))
        
        cv2.putText(img, str(person_name), (x+5,y-5), font, 1, (255,255,255), 2)
        cv2.putText(img, str(confidence), (x+5,y+h-5), font, 1, (255,255,0), 1)
        print(f"Detected face: {person_name} with confidence: {confidence}")
    
    # cv2.imshow('camera',img) - Removed due to GUI issues on Windows 

    k = cv2.waitKey(10) & 0xff # Press 'ESC' for exiting video
    if k == 27:
        break

# Do a bit of cleanup
print("Thanks for using this program, have a good day.")
cam.release()
cv2.destroyAllWindows()
