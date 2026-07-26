from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_cors import CORS
from blockchain import Blockchain
import cv2, os, joblib
import pandas as pd
import numpy as np
import base64
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"
CORS(app)
blockchain = Blockchain()

# ---------------- CONFIG ----------------
VOTING_START_HOUR =1   # 8 AM
VOTING_END_HOUR =12    # 8 PM (Adjust as needed)

@app.before_request
def check_voting_hours():
    # Allow static files to load even if closed
    if request.path.startswith('/static'):
        return None
        
    now = datetime.now()
    if now.hour < VOTING_START_HOUR or now.hour >= VOTING_END_HOUR:
        return f"""
        <div style="display:flex; justify-content:center; align-items:center; height:100vh; background:#1e1e2f; color:white; font-family:Arial; flex-direction:column;">
            <h1>🚫 Voting Closed</h1>
            <p>Operating Hours: {VOTING_START_HOUR}:00 - {VOTING_END_HOUR}:00</p>
            <p>Current Time: {now.strftime('%H:%M')}</p>
        </div>
        """

# ---------------- PATHS ----------------
try:
    from twilio.rest import Client
except ImportError:
    print("Twilio not found. Make sure to pip install twilio")
    Client = None

def send_sms(ref_code):
    # HARDCODED CREDENTIALS (PLACEHOLDERS)
    # User need to replace these with their own Twilio credentials
    sid = "AC_YOUR_ACCOUNT_SID"
    token = "YOUR_AUTH_TOKEN"
    from_number = "+1234567890" 
    to_number = "+919585119687"

    print(f"\n📲 [SMS] Sending to: {to_number}")
    print(f"📩 Content: Blockchain Ref Code: {ref_code}\n")



BASE = r"C:\Users\YESESWINI\Downloads\biometric_dataset"

# Load dataset
df = pd.read_csv(os.path.join(BASE,"aadhaar_biometric_data.csv"))

# Face recognition model
face_model = cv2.face.LBPHFaceRecognizer_create()
face_model.read(os.path.join(BASE,"face_model.yml"))

# 🔥 LOAD LABEL MAPPING
labels = joblib.load(os.path.join(BASE,"face_labels.pkl"))

# ---------------- GLOBALS ----------------
voted = {} # Dictionary {user_id: count}
used_fingerprints = set()

# ---------------- HOME PAGE ----------------
@app.route("/")
def home():
    # RESET DATA REMOVED - NOW PERSISTENT UNTIL MANUAL RESET
    return render_template("login.html")

# ---------------- VERIFICATION PAGE ----------------
@app.route("/verification")
def verification():
    return render_template("index.html")

# ---------------- VOTE STATUS VERIFY ----------------
@app.route("/verify")
def verify():
    return render_template("verify.html")

# ---------------- ADMIN LOGIN ----------------
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            return redirect(url_for("admin_verify"))
        else:
            error = "Invalid Credentials"

    return render_template("admin_login.html", error=error)

# ---------------- ADMIN VERIFY (MANUAL) ----------------
@app.route("/admin_verify", methods=["GET", "POST"])
def admin_verify():
    if request.method == "POST":
        aadhaar = request.form["aadhaar"]
        epic = request.form["epic"]

        # BYPASS CSV CHECK AS REQUESTED
        session["current_user"] = aadhaar # Use manual Aadhar
        session["fp_id"] = "ADMIN_MANUAL_" + epic # Dummy FP ID

        return redirect(url_for("vote"))

    return render_template("admin_verify.html")

# ---------------- PHONE FINGERPRINT ----------------
@app.route("/mobile_fp", methods=["POST"])
def mobile_fp():

    # Accept JSON OR plain text
    data = request.get_json(silent=True)

    if data and "fp_id" in data:
        fp_id = data["fp_id"]
    else:
        # fallback: raw text
        fp_id = request.data.decode("utf-8")

    if not fp_id:
        return jsonify({"msg":"invalid_data"})

    if fp_id in used_fingerprints:
        return jsonify({"msg":"fingerprint_used"})

    session["fp_ok"] = True
    session["fp_id"] = fp_id

    return jsonify({"msg":"success"})


# ---------------- FACE VERIFICATION ----------------
@app.route("/verify_face", methods=["POST"])
def verify_face():

    if "fp_ok" not in session:
        return "mobile_not_verified"

    try:
        data = request.get_json()

        if not data or "image" not in data:
            return "camera_failed"

        image_data = data["image"].split(",")[1]
        decoded = base64.b64decode(image_data)
        np_arr = np.frombuffer(decoded, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) == 0:
            return "no_face"

        (x,y,w,h) = faces[0]
        face_roi = gray[y:y+h, x:x+w]
        face_roi = cv2.resize(face_roi,(200,200))

        label, conf = face_model.predict(face_roi)

        # ✅ CORRECT PERSON FROM LABEL FILE
        person_id = labels[label]

        if voted.get(person_id, 0) >= 2:
            return "duplicate"

        session["current_user"] = person_id

        return redirect(url_for("details"))

    except Exception as e:
        print("Face Error:", e)
        return "camera_failed"

# ---------------- DETAILS PAGE ----------------
@app.route("/details")
def details():

    user = session.get("current_user")

    person = df[df["person_id"].astype(str)==str(user)].iloc[0]

    return render_template("details.html", person=person)

# ---------------- VOTE ----------------
@app.route("/vote", methods=["GET", "POST"])
def vote():
    if request.method == "GET":
        return render_template("vote.html")

    user = session.get("current_user")
    fp = session.get("fp_id")

    voted[user] = voted.get(user, 0) + 1
    used_fingerprints.add(fp)

    data = request.get_json()
    candidate = data["candidate"]
    ref_code = data.get("ref_code") # Optional storage

    block = blockchain.create_block(candidate, ref_code)
    print(f"\n✅ BLOCKCHAIN STORED: Vote for {candidate} with Ref Code: {ref_code}")
    print(f"   Block Hash: {block['hash']}\n")

    # Send SMS Notification
    send_sms(ref_code)

    session.clear()

    return jsonify({
        "message":"Vote stored",
        "hash":block["hash"]
    })

# ---------------- RESULT ----------------
@app.route("/result")
def result():
    return render_template("result.html")

# ---------------- BLOCKCHAIN ----------------
@app.route("/chain")
def chain():
    return jsonify(blockchain.chain)

# ---------------- RESET ELECTION ----------------
@app.route("/reset_election")
def reset_election():
    global blockchain, voted, used_fingerprints
    blockchain = Blockchain()
    voted = {}
    used_fingerprints = set()
    print("\n⚠️ ELECTION DATA RESET BY ADMIN\n")
    return redirect(url_for("home"))

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

