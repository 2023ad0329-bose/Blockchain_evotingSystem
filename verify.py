import cv2, joblib, os
import pandas as pd
import numpy as np

BASE = r"C:\Users\YESESWINI\Downloads\biometric_dataset"
CSV = os.path.join(BASE, "aadhaar_biometric_data.csv")

df = pd.read_csv(CSV)

fp_model = joblib.load(os.path.join(BASE, "fingerprint_model.pkl"))

face_model = cv2.face.LBPHFaceRecognizer_create()
face_model.read(os.path.join(BASE, "face_model.yml"))

labels = joblib.load(os.path.join(BASE, "face_labels.pkl"))


voted = set()

# -------- Fingerprint ----------
img = cv2.imread(os.path.join(r"C:\Users\YESESWINI\Downloads\biometric_dataset\fingerprints\test_fp.png"), 0)

if img is None:
    print("❌ test_fp.png not found")
    exit()

img = cv2.resize(img,(128,128)).flatten().reshape(1,-1)
pred = fp_model.predict(img)
person_id = labels[pred[0]]

# -------- Face ----------
cam = cv2.VideoCapture(0)
ret, frame = cam.read()
gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
gray = cv2.resize(gray,(200,200))

label, conf = face_model.predict(gray)
cam.release()

if labels[label] == person_id:

    if person_id in voted:
        print("❌ Already Voted!")
    else:
        voted.add(person_id)

        person = df[df["person_id"]==person_id]
        print("✅ VERIFIED")
        print(person[["name","gender","aadhaar_number"]])

        print("\n--- EVM ---")
        print("1. Party A\n2. Party B\n3. Party C")
else:
    print("❌ Face & Fingerprint mismatch")
