import os
import cv2
import numpy as np
import pandas as pd
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import joblib

BASE = r"C:\Users\YESESWINI\Downloads\biometric_dataset"
CSV = os.path.join(BASE, "aadhaar_biometric_data.csv")
FP_DIR = os.path.join(BASE, "fingerprints")

df = pd.read_csv(CSV)

X = []
y = []

for i, row in df.iterrows():
    img = cv2.imread(os.path.join(BASE, row["fingerprint_image"]), 0)
    img = cv2.resize(img, (128,128))
    X.append(img.flatten())
    y.append(row["person_id"])

X = np.array(X)
y = LabelEncoder().fit_transform(y)

model = SVC(kernel="linear", probability=True)
model.fit(X, y)

joblib.dump(model, os.path.join(BASE, "fingerprint_model.pkl"))

print("✅ Fingerprint model trained & saved in Downloads folder")
