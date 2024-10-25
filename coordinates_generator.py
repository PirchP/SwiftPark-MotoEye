import cv2
import yaml

class CoordinatesGenerator:
    def __init__(self, image_file, data_file):
        self.image_file = image_file
        self.data_file = data_file
        self.coordinates = []
        self.click_count = 0
        self.slot_number = 1
        self.image = cv2.imread(image_file).copy()
        self.original_image = self.image.copy()

    def click_event(self, event, x, y, flags, params):
        if event == cv2.EVENT_LBUTTONDOWN:
            print(f"คลิกที่: {x}, {y}")
            self.coordinates.append([x, y])
            self.click_count += 1

            cv2.circle(self.image, (x, y), 5, (0, 255, 0), -1)
            cv2.imshow("Image", self.image)

            if self.click_count == 4:
                self.draw_polygon()
                self.save_coordinates()
                self.click_count = 0
                self.coordinates = []

    def draw_polygon(self):
        if len(self.coordinates) == 4:
            points = self.coordinates
            cv2.line(self.image, tuple(points[0]), tuple(points[1]), (0, 255, 0), 2)
            cv2.line(self.image, tuple(points[1]), tuple(points[2]), (0, 255, 0), 2)
            cv2.line(self.image, tuple(points[2]), tuple(points[3]), (0, 255, 0), 2)
            cv2.line(self.image, tuple(points[3]), tuple(points[0]), (0, 255, 0), 2)

            center_x = int(sum([point[0] for point in points]) / 4)
            center_y = int(sum([point[1] for point in points]) / 4)
            cv2.putText(self.image, str(self.slot_number), (center_x - 10, center_y), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)

            self.slot_number += 1
            cv2.imshow("Image", self.image)

    def save_coordinates(self):
        try:
            with open(self.data_file, 'r') as file:
                existing_data = yaml.safe_load(file) or []
        except FileNotFoundError:
            existing_data = []

        new_id = len(existing_data) + 1
        existing_data.append({'id': new_id, 'coordinates': self.coordinates})

        with open(self.data_file, 'w') as file:
            yaml.dump(existing_data, file, default_flow_style=False)

        print(f"บันทึกพิกัด: {self.coordinates}")

    def reset_image_and_file(self):
        self.image = self.original_image.copy()
        self.coordinates = []
        self.click_count = 0
        self.slot_number = 1

        with open(self.data_file, 'w') as file:
            file.write('')
        print("ล้างข้อมูลในไฟล์ coordinates.yml เรียบร้อยแล้ว")
        cv2.imshow("Image", self.image)

    def generate(self):
        if self.image is None:
            print("Error: ไม่สามารถโหลดภาพได้")
            return
        cv2.imshow("Image", self.image)
        cv2.setMouseCallback("Image", self.click_event)

        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                self.reset_image_and_file()

        cv2.destroyAllWindows()

if __name__ == "__main__":
    generator = CoordinatesGenerator('moto.png', 'coordinates.yml')
    generator.generate()
