import cv2
import os

# Resolve paths relative to this script so files don't end up in the wrong cwd.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLES_DIR = os.path.join(BASE_DIR, 'samples')

# Create samples directory if it doesn't exist
os.makedirs(SAMPLES_DIR, exist_ok=True)

cam = cv2.VideoCapture(0, cv2.CAP_DSHOW) #create a video capture object which is helpful to capture videos through webcam
cam.set(3, 640) # set video FrameWidth
cam.set(4, 480) # set video FrameHeight


detector = cv2.CascadeClassifier(cv2.data.haarcascades+'haarcascade_frontalface_default.xml')
#Haar Cascade classifier is an effective object detection approach

face_id = input("Enter a Numeric user ID here: ").strip()
if not face_id.isdigit():
    print("Error: User ID must be numeric (example: 7).")
    cam.release()
    cv2.destroyAllWindows()
    raise SystemExit(1)
#Use integer ID for every new face (0,1,2,3,4,5,6,7,8,9........)

print("Taking samples, look at camera ....... ")
count = 0 # Initializing sampling face count

while True:

    ret, img = cam.read() #read the frames using the above created object
    converted_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) #The function converts an input image from one color space to another
    faces = detector.detectMultiScale(converted_image, 1.3, 5)

    for (x,y,w,h) in faces:

        cv2.rectangle(img, (x,y), (x+w,y+h), (255,0,0), 2) #used to draw a rectangle on any image
        count += 1

        
        file_name = f"face.{face_id}.{count}.jpg"
        file_path = os.path.join(SAMPLES_DIR, file_name)
        cv2.imwrite(file_path, converted_image[y:y+h, x:x+w])
        # To capture & Save images into the datasets folder
        print(f"Sample {count} captured for user {face_id}")

    k = cv2.waitKey(100) & 0xff # Waits for a pressed key
    if k == 27: # Press 'ESC' to stop
        break
    elif count >= 10: # Take 50 sample (More sample --> More accuracy)
         break

print("Samples taken now closing the program....")
cam.release()
cv2.destroyAllWindows()
