import cv2 as open_cv
import numpy as np
import logging
import json
from drawing_utils import draw_contours

class MotionDetector:
    # ค่าคงที่สำหรับการตรวจจับการเคลื่อนไหว
    LAPLACIAN = 1.7  # ค่าความไวในการตรวจจับความเคลื่อนไหว
    DETECT_DELAY = 2  # ดีเลย์ในการตรวจจับ 

    # ฟังก์ชันเริ่มต้นสำหรับการตั้งค่าเริ่มต้นของคลาส
    def __init__(self, video, coordinates, start_frame):
        self.video = video  
        self.coordinates_data = coordinates  
        self.start_frame = start_frame  
        self.contours = []  # รูปร่างของช่องจอด
        self.bounds = []  # ขอบเขตของแต่ละช่องจอด
        self.mask = []  
        self.occupied_slots = []  

        capture = open_cv.VideoCapture(self.video)
        self.video_width = int(capture.get(open_cv.CAP_PROP_FRAME_WIDTH))  
        self.video_height = int(capture.get(open_cv.CAP_PROP_FRAME_HEIGHT))  
        capture.release()  

    # ฟังก์ชันหลักที่ใช้ในการตรวจจับการเคลื่อนไหว
    def detect_motion(self):
        capture = open_cv.VideoCapture(self.video)  
        capture.set(open_cv.CAP_PROP_POS_FRAMES, self.start_frame)  
        coordinates_data = self.coordinates_data  

        # วนลูปเพื่อสร้าง(mask) 
        for p in coordinates_data:
            coordinates = self._coordinates(p)  # แปลงพิกัดช่องจอดรถ
            if coordinates is None:
                logging.error(f"ไม่สามารถแปลงพิกัดได้สำหรับ id: {p['id']}")  # ถ้าแปลงพิกัดไม่ได้ให้แจ้งข้อผิดพลาด
                continue

            # สร้างขอบเขต (bounding box) รอบพื้นที่ของช่องจอด
            rect = open_cv.boundingRect(coordinates)
            self.bounds.append(rect)

            # ปรับพิกัดให้เหมาะสมสำหรับหน้ากาก
            new_coordinates = coordinates.copy()
            new_coordinates[:, 0] -= rect[0]
            new_coordinates[:, 1] -= rect[1]

            # สร้างหน้ากากช่องจอดรถ
            mask = open_cv.drawContours(
                np.zeros((rect[3], rect[2]), dtype=np.uint8),
                [new_coordinates],
                contourIdx=-1,
                color=255,
                thickness=-1,
                lineType=open_cv.LINE_8
            )
            mask = mask == 255
            self.mask.append(mask)

        statuses = [False] * len(coordinates_data) 
        print("เริ่มการตรวจจับการเคลื่อนไหวใน")

        # วนลูปตรวจจับการเคลื่อนไหวในแต่ละเฟรมของวิดีโอ
        while True:
            result, frame = capture.read()  # อ่านเฟรมจากวิดีโอ
            if not result:
                capture.set(open_cv.CAP_PROP_POS_FRAMES, self.start_frame)
                continue

            frame_height, frame_width = frame.shape[:2]
            blurred = open_cv.GaussianBlur(frame.copy(), (7, 7), 3)  
            grayed = open_cv.cvtColor(blurred, open_cv.COLOR_BGR2GRAY)  

            # ตรวจสอบแต่ละช่องจอดรถ
            for index, c in enumerate(coordinates_data):
                # ปรับสเกลให้ตรงกับวิดีโอที่ถูกดึงมา
                scale_x = frame_width / self.video_width
                scale_y = frame_height / self.video_height
                coordinates = self._coordinates(c)
                coordinates[:, 0] = coordinates[:, 0] * scale_x
                coordinates[:, 1] = coordinates[:, 1] * scale_y

                # ใช้ฟังก์ชันตรวจสอบการเปลี่ยนแปลง
                status = self.__apply(grayed, index, c)

                # เลือกสีและข้อความตามสถานะของช่องจอด
                color = (0, 0, 255) if status else (0, 255, 0)  
                label = "Occupied" if status else "Available"  

                rect = self.bounds[index]
                top_left = (int(rect[0] * scale_x), int(rect[1] * scale_y))
                bottom_right = (int((rect[0] + rect[2]) * scale_x), int((rect[1] + rect[3]) * scale_y))

                # วาดกรอบรอบช่องจอดรถ
                open_cv.rectangle(frame, top_left, bottom_right, color, 2)
                open_cv.putText(frame, str(index + 1), (top_left[0] + 10, top_left[1] + 30), open_cv.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

                # วาดสถานะ (Occupied/Available)
                center_x = int((top_left[0] + bottom_right[0]) / 2)
                center_y = int((top_left[1] + bottom_right[1]) / 2)
                open_cv.putText(frame, label, (center_x, center_y + 30), open_cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                # เช็คว่าสถานะของช่องจอดเปลี่ยนแปลงหรือไม่
                if self.status_changed(statuses, index, status):
                    print(f"สถานะของช่องจอด ID {c['id']} เปลี่ยนเป็น {'Occupied' if status else 'Available'}")
                    update_parking_status(c['id'], status)
                    statuses[index] = status

            open_cv.imshow("Parking Detection", frame)  # แสดงเฟรมปัจจุบัน

            if open_cv.waitKey(1) & 0xFF == ord("q"):
                break  # หยุดโปรแกรมถ้ากด "q"

        capture.release()
        open_cv.destroyAllWindows()

    # ฟังก์ชันตรวจจับการเคลื่อนไหวในแต่ละช่องจอด
    def __apply(self, grayed, index, p):
        coordinates = self._coordinates(p)
        if coordinates is None:
            logging.error(f"ไม่สามารถแปลงพิกัดได้สำหรับ id: {p['id']}")
            return False

        rect = self.bounds[index]
        roi_gray = grayed[rect[1]:(rect[1] + rect[3]), rect[0]:(rect[0] + rect[2])]

        if roi_gray.size == 0:
            logging.error(f"roi_gray ว่างสำหรับ id: {p['id']}")
            return False

        mask = self.mask[index]
        if roi_gray.shape != mask.shape:
            mask = open_cv.resize(mask, (roi_gray.shape[1], roi_gray.shape[0]))

        laplacian = open_cv.Laplacian(roi_gray, open_cv.CV_64F)  # คำนวณ laplacian เพื่อหาการเปลี่ยนแปลงในภาพ

        coordinates[:, 0] -= rect[0]
        coordinates[:, 1] -= rect[1]

        # ตรวจสอบว่ามีการเปลี่ยนแปลงเพียงพอที่จะบอกว่าถูกจอดหรือไม่
        status = np.mean(np.abs(laplacian * mask)) > MotionDetector.LAPLACIAN
        return status

    # ฟังก์ชันแปลงพิกัดจาก JSON ไปยัง NumPy array
    @staticmethod
    def _coordinates(p):
        try:
            return np.array(p['coordinates'], dtype=np.int32)
        except KeyError:
            logging.error("Error: พิกัดไม่ถูกต้องหรือไม่พบพิกัดในข้อมูล")
            return None

    # ฟังก์ชันตรวจสอบว่ามีการเปลี่ยนแปลงสถานะหรือไม่
    def status_changed(self, statuses, index, new_status):
        if index < len(statuses):
            return statuses[index] != new_status
        return False

# ฟังก์ชันอัปเดตสถานะที่จอดรถลงในไฟล์ JSON
def update_parking_status(slot_id, status):
    try:
        with open('parking_status.json', 'r') as file:
            parking_status = json.load(file)
    except FileNotFoundError:
        parking_status = []

    if isinstance(status, bool) is False:
        status = bool(status)

    slot_found = False
    for slot in parking_status:
        if slot['id'] == slot_id:
            slot['occupied'] = status
            slot_found = True
            break

    if not slot_found:
        parking_status.append({"id": slot_id, "occupied": status})

    with open('parking_status.json', 'w') as file:
        json.dump(parking_status, file, indent=4)

    print(f"สถานะที่จอดรถ ID {slot_id} ถูกบันทึกเป็น {'Occupied' if status else 'Available'}")
