import cv2
from tracking.hand_tracker import HandTracker


def main():
    # Открываем камеру (если не работает — попробуй 1 вместо 0)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Не удалось открыть камеру")
        return

    tracker = HandTracker()

    # 🔹 Создаём изменяемое окно
    cv2.namedWindow("Hand Tracking", cv2.WINDOW_NORMAL)

    # 🔹 Задаём начальный размер окна
    cv2.resizeWindow("Hand Tracking", 960, 540)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Не удалось получить кадр")
            break

        # Обработка руки
        frame, landmarks = tracker.process(frame)

        # Можно вывести координаты указательного пальца
        # if landmarks:
            # print("Index tip:", landmarks[8])  # 8 — кончик указательного

        # Показываем кадр
        cv2.imshow("Hand Tracking", frame)

        # Выход по нажатию Q
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()