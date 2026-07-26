import os
import cv2
import pandas as pd
import numpy as np
import joblib

BASE = r"C:\Users\YESESWINI\Downloads\biometric_dataset"
CSV = os.path.join(BASE, "aadhaar_biometric_data.csv")

df = pd.read_csv(CSV)

faces = []
labels = []

label_map = {}
count = 0

for i, row in df.iterrows():
    img = cv2.imread(os.path.join(BASE, row["face_image"]), 0)
    img = cv2.resize(img, (200,200))

    faces.append(img)
    labels.append(count)
    label_map[count] = row["person_id"]
    count += 1

model = cv2.face.LBPHFaceRecognizer_create()
model.train(faces, np.array(labels))

model.save(os.path.join(BASE, "face_model.yml"))
joblib.dump(label_map, os.path.join(BASE, "face_labels.pkl"))

print("✅ Face model trained & saved in Downloads folder")
