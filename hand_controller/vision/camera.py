import cv2


class Camera:
    def __init__(self, camera_id=0, window_name="Hand Tracking"):
        self.cap = cv2.VideoCapture(camera_id)
        self.window_name = window_name
        
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        print(f"Camera FPS: {fps}")
        
        if not self.cap.isOpened():
            raise RuntimeError("Failed to open camera.")
    
            # Use actual camera resolution instead of hardcoded values
        w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, w, h)

    def read(self):
        """Reads and returns the next frame. Raises RuntimeError if frame cannot be read."""
        ret, frame = self.cap.read()
        if not ret:
            raise RuntimeError("Failed to read frame from camera.")
        return frame

    def show(self, frame):
        """Displays a frame in the camera window."""
        cv2.imshow(self.window_name, frame)

    def should_quit(self):
        """Returns True if the user pressed 'q'."""
        return cv2.waitKey(1) & 0xFF == ord('q')

    def release(self):
        """Releases the camera and destroys all windows."""
        self.cap.release()
        cv2.destroyAllWindows()

    