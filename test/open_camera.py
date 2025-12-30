import cv2

max_cameras = 1
caps = {}

# Detect and open cameras
for i in range(0, max_cameras):
    cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
    if not cap.isOpened():
        continue

    ret, frame = cap.read()
    if not ret:
        cap.release()
        continue

    caps[i] = cap
    print(f"Camera index {i:02d} OK!")

print(f"Cameras found: {list(caps.keys())}")

# Show camera feeds
while True:
    for i, cap in caps.items():
        ret, frame = cap.read()
        if ret:
            cv2.imshow(f"Camera {i}", frame)

    # Press q to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
for cap in caps.values():
    cap.release()

cv2.destroyAllWindows()
