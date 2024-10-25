import yaml
import json
import threading
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from motion_detector import MotionDetector

VIDEO_SOURCE = "moto.mov"
PARKING_COORDINATES = "coordinates.yml"
START_FRAME = 0
PARKING_STATUS_FILE = "parking_status.json"

# ฟังก์ชันสำหรับล้างสถานะช่องจอด
def clear_parking_status():
    with open(PARKING_STATUS_FILE, 'w') as file:
        json.dump([], file)
    print(f"ล้างข้อมูลในไฟล์ {PARKING_STATUS_FILE} เรียบร้อยแล้ว")

# ฟังก์ชันสำหรับโหลดพิกัดช่องจอดจากไฟล์
def load_coordinates():
    try:
        with open(PARKING_COORDINATES, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print("ไม่พบไฟล์ coordinates.yml")
        return []

# ฟังก์ชันสำหรับตรวจจับการเคลื่อนไหว
def run_motion_detector():
    clear_parking_status()
    parking_slots = load_coordinates()

    if not parking_slots:
        print("ไม่มีข้อมูลพิกัดช่องจอดรถ")
    else:
        detector = MotionDetector(VIDEO_SOURCE, parking_slots, START_FRAME)
        detector.detect_motion()

# สร้างแอป Flask
app = Flask(__name__)
CORS(app)  # เปิดใช้งาน CORS สำหรับทุก route

# ให้บริการไฟล์ parking_status.json ผ่าน API
@app.route('/parking_status.json')
def parking_status():
    try:
        with open(PARKING_STATUS_FILE) as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "ไฟล์ parking_status.json ไม่พบ"}), 404

# ให้บริการหน้าเว็บ index.html
@app.route('/<path:filename>')
def serve_static_files(filename):
    return send_from_directory('', filename)

if __name__ == "__main__":
    # รันการตรวจจับการเคลื่อนไหวใน thread แยก
    motion_thread = threading.Thread(target=run_motion_detector)
    motion_thread.start()

    # รันเซิร์ฟเวอร์ Flask ใน thread หลัก
    app.run(debug=True, port=5000)
