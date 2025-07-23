import cv2
import numpy as np
import tensorflow as tf

# 解像度やFPSの設定
WIDTH = 1280
HEIGHT = 720
FPS = 30.0  # 適切な値に調整

# カメラの初期化
camera = cv2.VideoCapture(0)  # 0はデバイスのカメラID
camera.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
camera.set(cv2.CAP_PROP_FPS, FPS)

# モデルとラベルファイルのパス
MODEL_PATH = "ssd_mobilenet_v2_coco/saved_model"
LABEL_PATH = "coco_labels.txt"

# ラベル読み込み
with open(LABEL_PATH, "r") as f:
    labels = f.read().splitlines()

# モデル読み込み
model = tf.saved_model.load(MODEL_PATH)
infer = model.signatures["serving_default"]

# カメラの初期化
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 入力データを準備
    input_tensor = tf.convert_to_tensor(frame[None, ...], dtype=tf.uint8)

    # 推論実行
    detections = infer(input_tensor)

    # 検出結果の取得
    for i in range(int(detections["num_detections"])):
        score = detections["detection_scores"][0][i].numpy()
        if score > 0.5:
            bbox = detections["detection_boxes"][0][i].numpy()
            class_id = int(detections["detection_classes"][0][i].numpy())

            # ボックス描画
            h, w, _ = frame.shape
            y1, x1, y2, x2 = (bbox * [h, w, h, w]).astype(int)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, labels[class_id], (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # 映像表示
    cv2.imshow("MobileNet SSD", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()