import cv2

# 解像度やFPSの設定
WIDTH = 1280
HEIGHT = 720
FPS = 30.0  # 適切な値に調整

# カメラの初期化
camera = cv2.VideoCapture(0)  # 0はデバイスのカメラID
camera.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
camera.set(cv2.CAP_PROP_FPS, FPS)

# カメラが正常に初期化できているか確認
if not camera.isOpened():
    print("カメラが開けませんでした。")
    exit()

print("カメラが正常に開きました。Qキーで終了します。")

# ループでカメラ映像を取得
while True:
    ret, frame = camera.read()
    if not ret:
        print("フレームの取得に失敗しました。")
        break

    # 映像を表示
    cv2.imshow("Live Camera", frame)

    # 'q'キーで終了
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("終了します。")
        break

# 後処理
camera.release()
cv2.destroyAllWindows()