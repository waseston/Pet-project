import cv2

class Camera:
    def __init__(self, camera_id=0):
        self.cap = cv2.VideoCapture(camera_id)

        if not self.cap.isOpened():
            raise RuntimeError("Не удалось открыть камеру")

    def run(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Не удалось получить кадр")
                break

            cv2.imshow("Camera", frame)

            # Выход по клавише Q
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()
