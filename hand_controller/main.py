from vision.camera import Camera

def main():
    cam = Camera(camera_id=0)  # попробуй 0, если не работает — 1
    cam.run()

if __name__ == "__main__":
    main()
