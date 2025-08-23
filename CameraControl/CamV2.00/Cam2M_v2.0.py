# Cam2M_v2.0.py
# Camera control with GUI: live preview, interval still capture, and timelapse creation/playback
# Requirements: opencv-python, pillow
# Tested on: Windows (webcam). Paths use Windows-style backslashes.

import os
import cv2
import time
import glob
import threading
from datetime import datetime

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False


class CameraController:
    def __init__(self):
        self.cap = None
        self.device_index = 0
        self.width = 1280
        self.height = 720
        self.fps = 30
        self.preview_running = False
        self.capture_enabled = False
        self.capture_interval_sec = 10
        self.next_capture_time = None
        self.output_dir = os.path.abspath("Captured")
        os.makedirs(self.output_dir, exist_ok=True)

        self.last_frame = None
        self.lock = threading.Lock()

    def open_camera(self, device_index: int, width: int, height: int, fps: int) -> bool:
        self.device_index = device_index
        self.width = width
        self.height = height
        self.fps = fps
        if self.cap is not None:
            self.release_camera()
        cap = cv2.VideoCapture(device_index)
        # Apply properties (might be best-effort depending on driver)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2.CAP_PROP_FPS, fps)
        ok, _ = cap.read()
        if not ok:
            cap.release()
            return False
        self.cap = cap
        return True

    def read_frame(self):
        if self.cap is None:
            return None
        ok, frame = self.cap.read()
        if not ok:
            return None
        with self.lock:
            self.last_frame = frame
        return frame

    def get_last_frame(self):
        with self.lock:
            return None if self.last_frame is None else self.last_frame.copy()

    def start_preview(self):
        self.preview_running = True
        self.next_capture_time = time.time() + self.capture_interval_sec

    def stop_preview(self):
        self.preview_running = False

    def enable_auto_capture(self, enabled: bool, interval_sec: int):
        self.capture_enabled = enabled
        self.capture_interval_sec = max(1, int(interval_sec))
        self.next_capture_time = time.time() + self.capture_interval_sec

    def save_current_frame(self) -> str:
        frame = self.get_last_frame()
        if frame is None:
            return ""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"img_{ts}.jpg"
        path = os.path.join(self.output_dir, filename)
        # Use high-quality JPEG
        try:
            cv2.imwrite(path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
            return path
        except Exception:
            return ""

    def tick_auto_capture(self):
        if not (self.preview_running and self.capture_enabled):
            return None
        now = time.time()
        if self.next_capture_time is None:
            self.next_capture_time = now + self.capture_interval_sec
            return None
        if now >= self.next_capture_time:
            saved = self.save_current_frame()
            self.next_capture_time = now + self.capture_interval_sec
            return saved
        return None

    def release_camera(self):
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

    def __del__(self):
        self.release_camera()


class TimelapseCreator:
    def __init__(self, source_dir: str):
        self.source_dir = source_dir
        self.last_output_path = None

    def _find_images(self):
        # Find jpg/jpeg/png sorted by filename (timestamped)
        exts = ["*.jpg", "*.jpeg", "*.png"]
        files = []
        for ext in exts:
            files.extend(glob.glob(os.path.join(self.source_dir, ext)))
        files.sort()
        return files

    def create_timelapse(self, output_fps: int = 24, output_name: str | None = None, size_hint: tuple[int, int] | None = None, progress_callback=None):
        images = self._find_images()
        if not images:
            raise RuntimeError("No images found in the output folder.")
        first = cv2.imread(images[0])
        if first is None:
            raise RuntimeError("Failed to read the first image.")
        h, w = first.shape[:2]
        if size_hint is not None:
            w, h = size_hint
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        if output_name is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"timelapse_{ts}.mp4"
        out_path = os.path.join(self.source_dir, output_name)
        writer = cv2.VideoWriter(out_path, fourcc, max(1, output_fps), (w, h))
        total = len(images)
        for i, img_path in enumerate(images, 1):
            img = cv2.imread(img_path)
            if img is None:
                continue
            ih, iw = img.shape[:2]
            if (iw, ih) != (w, h):
                img = cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA)
            writer.write(img)
            if progress_callback:
                try:
                    progress_callback(i, total)
                except Exception:
                    pass
        writer.release()
        self.last_output_path = out_path
        return out_path

    def play_timelapse(self, video_path: str | None = None, wait_ms: int = 33):
        path = video_path or self.last_output_path
        if not path or not os.path.exists(path):
            raise RuntimeError("No timelapse video available to play.")
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            raise RuntimeError("Failed to open the video file.")
        window_name = f"Timelapse: {os.path.basename(path)} (press 'q' to quit)"
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            cv2.imshow(window_name, frame)
            key = cv2.waitKey(wait_ms) & 0xFF
            if key == ord('q') or key == 27:
                break
        cap.release()
        cv2.destroyWindow(window_name)


class CameraApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cam2M v2.0 - Interval Capture & Timelapse")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.geometry("980x720")

        if not PIL_AVAILABLE:
            messagebox.showwarning(
                "Pillow not found",
                "Pillow (PIL) is not installed. The preview window may not work.\n"
                "Install via: pip install pillow"
            )

        self.cam = CameraController()
        self.tl = TimelapseCreator(self.cam.output_dir)

        self._build_ui()
        self.preview_job = None

    def _build_ui(self):
        root = self
        # Controls frame
        ctrl = ttk.Frame(root)
        ctrl.pack(side=tk.TOP, fill=tk.X, padx=8, pady=8)

        # Device index
        ttk.Label(ctrl, text="Device").grid(row=0, column=0, sticky=tk.W)
        self.device_var = tk.IntVar(value=0)
        ttk.Spinbox(ctrl, from_=0, to=5, width=5, textvariable=self.device_var).grid(row=0, column=1, sticky=tk.W, padx=4)

        # Resolution
        ttk.Label(ctrl, text="Resolution (WxH)").grid(row=0, column=2, sticky=tk.W)
        self.width_var = tk.IntVar(value=1280)
        self.height_var = tk.IntVar(value=720)
        ttk.Entry(ctrl, width=6, textvariable=self.width_var).grid(row=0, column=3, padx=2)
        ttk.Label(ctrl, text="x").grid(row=0, column=4)
        ttk.Entry(ctrl, width=6, textvariable=self.height_var).grid(row=0, column=5, padx=2)

        # FPS
        ttk.Label(ctrl, text="FPS").grid(row=0, column=6, sticky=tk.W)
        self.fps_var = tk.IntVar(value=30)
        ttk.Entry(ctrl, width=5, textvariable=self.fps_var).grid(row=0, column=7, padx=4)

        # Interval capture
        ttk.Label(ctrl, text="Capture Interval (sec)").grid(row=1, column=0, sticky=tk.W, pady=(6, 0))
        self.interval_var = tk.IntVar(value=10)
        ttk.Entry(ctrl, width=6, textvariable=self.interval_var).grid(row=1, column=1, sticky=tk.W, pady=(6, 0))

        # Output dir
        ttk.Label(ctrl, text="Output Folder").grid(row=1, column=2, sticky=tk.W, pady=(6, 0))
        self.output_var = tk.StringVar(value=self.cam.output_dir)
        ttk.Entry(ctrl, width=40, textvariable=self.output_var).grid(row=1, column=3, columnspan=3, sticky=tk.W+tk.E, pady=(6, 0))
        ttk.Button(ctrl, text="Browse", command=self.browse_output).grid(row=1, column=6, columnspan=2, sticky=tk.W, pady=(6, 0))

        # Timelapse FPS
        ttk.Label(ctrl, text="Timelapse FPS").grid(row=2, column=0, sticky=tk.W, pady=(6, 0))
        self.tl_fps_var = tk.IntVar(value=24)
        ttk.Entry(ctrl, width=6, textvariable=self.tl_fps_var).grid(row=2, column=1, sticky=tk.W, pady=(6, 0))

        # Buttons
        btns = ttk.Frame(root)
        btns.pack(side=tk.TOP, fill=tk.X, padx=8, pady=4)
        ttk.Button(btns, text="Start Preview", command=self.start_preview).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Stop Preview", command=self.stop_preview).pack(side=tk.LEFT, padx=4)
        ttk.Separator(btns, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=4)
        ttk.Button(btns, text="Start Auto Capture", command=self.start_capture).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Stop Auto Capture", command=self.stop_capture).pack(side=tk.LEFT, padx=4)
        ttk.Separator(btns, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=4)
        ttk.Button(btns, text="Create Timelapse", command=self.create_timelapse).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Play Timelapse", command=self.play_timelapse).pack(side=tk.LEFT, padx=4)

        # Status
        self.status_var = tk.StringVar(value="Idle")
        ttk.Label(root, textvariable=self.status_var, anchor=tk.W).pack(side=tk.TOP, fill=tk.X, padx=8, pady=4)

        # Preview area
        self.preview_label = ttk.Label(root, text="Preview will appear here")
        self.preview_label.pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=8, pady=8)

        # Progress bar for timelapse
        self.progress = ttk.Progressbar(root, orient=tk.HORIZONTAL, mode='determinate')
        self.progress.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=8)

    def browse_output(self):
        chosen = filedialog.askdirectory(initialdir=self.output_var.get())
        if chosen:
            self.output_var.set(chosen)
            self.cam.output_dir = chosen
            self.tl.source_dir = chosen

    def start_preview(self):
        if self.preview_job is not None:
            return
        device = int(self.device_var.get())
        w = int(self.width_var.get())
        h = int(self.height_var.get())
        fps = int(self.fps_var.get())
        if not self.cam.open_camera(device, w, h, fps):
            messagebox.showerror("Camera Error", "Failed to open camera. Try another device index or resolution.")
            return
        self.cam.start_preview()
        self.status_var.set(f"Preview started (Device {device}, {w}x{h}@{fps}fps)")
        self._loop_preview()

    def stop_preview(self):
        if self.preview_job is not None:
            try:
                self.after_cancel(self.preview_job)
            except Exception:
                pass
            self.preview_job = None
        self.cam.stop_preview()
        self.cam.release_camera()
        self.status_var.set("Preview stopped")

    def start_capture(self):
        interval = max(1, int(self.interval_var.get()))
        self.cam.enable_auto_capture(True, interval)
        self.status_var.set(f"Auto capture enabled (every {interval}s)")

    def stop_capture(self):
        self.cam.enable_auto_capture(False, max(1, int(self.interval_var.get())))
        self.status_var.set("Auto capture disabled")

    def _loop_preview(self):
        if not self.cam.preview_running:
            self.preview_job = None
            return
        frame = self.cam.read_frame()
        saved_path = self.cam.tick_auto_capture()
        if saved_path:
            self.status_var.set(f"Saved: {os.path.basename(saved_path)}")
        if frame is not None and PIL_AVAILABLE:
            # Convert BGR to RGB and show in Tkinter
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            # Fit image into the label while keeping aspect ratio
            lbl_w = max(320, self.preview_label.winfo_width())
            lbl_h = max(240, self.preview_label.winfo_height())
            img = img.resize(self._fit_size(img.size, (lbl_w, lbl_h)), Image.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=img)
            self.preview_label.imgtk = imgtk  # keep reference
            self.preview_label.configure(image=imgtk, text="")
        elif frame is None:
            # Try to reopen if disconnected
            pass
        # Schedule next frame update ~ every 10-20 ms depending on FPS
        delay = max(10, int(1000 / max(1, self.cam.fps)))
        self.preview_job = self.after(delay, self._loop_preview)

    @staticmethod
    def _fit_size(src_size, box_size):
        sw, sh = src_size
        bw, bh = box_size
        scale = min(bw / sw, bh / sh)
        return max(1, int(sw * scale)), max(1, int(sh * scale))

    def _update_progress(self, current, total):
        self.progress.configure(maximum=total, value=current)
        self.progress.update_idletasks()

    def create_timelapse(self):
        fps = max(1, int(self.tl_fps_var.get()))
        try:
            self.progress.configure(value=0)
            out = self.tl.create_timelapse(output_fps=fps, progress_callback=self._update_progress)
            self.status_var.set(f"Timelapse created: {out}")
            messagebox.showinfo("Timelapse", f"Timelapse created:\n{out}")
        except Exception as e:
            messagebox.showerror("Timelapse Error", str(e))
        finally:
            self.progress.configure(value=0)

    def play_timelapse(self):
        # Prefer last output; if not available, ask user
        path = self.tl.last_output_path
        if not path or not os.path.exists(path):
            path = filedialog.askopenfilename(
                title="Select timelapse video",
                filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")],
                initialdir=self.output_var.get(),
            )
        if not path:
            return
        try:
            # Estimate wait from the video's FPS
            cap = cv2.VideoCapture(path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            cap.release()
            wait_ms = int(1000 / fps) if fps and fps > 0 else 33
            self.tl.play_timelapse(video_path=path, wait_ms=wait_ms)
        except Exception as e:
            messagebox.showerror("Playback Error", str(e))

    def on_close(self):
        self.stop_capture()
        self.stop_preview()
        self.destroy()


def main():
    app = CameraApp()
    app.mainloop()


if __name__ == "__main__":
    main()
