import cv2

# HOG人検出器を初期化
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

# USBカメラの映像を取得
camera = cv2.VideoCapture(0)  # デバイスIDを指定（必要に応じて0以外を設定）

if not camera.isOpened():
    print("カメラを認識できませんでした。")
    exit()

while True:
    ret, frame = camera.read()
    if not ret:
        break

    # 人を検出
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    boxes, weights = hog.detectMultiScale(gray, winStride=(8, 8))

    # 検出結果を描画
    for (x, y, w, h) in boxes:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # 映像を表示
    cv2.imshow("人検出", frame)

    # 'q'キーで終了
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# リソース解放
camera.release()
cv2.destroyAllWindows()
