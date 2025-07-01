import sys
import av
import os
import numpy as np
import pandas as pd
import pyqtgraph as pg
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QSlider,
    QHBoxLayout, QCheckBox, QGroupBox, QComboBox, QGridLayout,
    QProgressBar, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
import cv2

class TimeAxisItem(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        return [f"{int(v//60)}:{int(v%60):02d}" for v in values]


class VideoIMUPlayer(QWidget):
    def __init__(self):
        self.base_path = r"C:\\Users\\s4659771\\Documents\\MyTurn_Project\\Data\\Processed"
        self.imu_base_path = r"C:\\Users\\s4659771\\Documents\\MyTurn_Project\\Data\\ReadyToAnalyse"
        self.zoom_window_sec = 5
        super().__init__()
        self.signal_curves = {}
        self.signals = {}
        self.signal_checkboxes = {}
        self.camera_paths = {}
        self.initUI()

        self.container = None
        self.stream = None
        self.fps = 60
        self.frames = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.current_frame_idx = 0

        self.imu_data = None
        self.time = None

    def initUI(self):
        layout = QVBoxLayout()

        dropdown_layout = QHBoxLayout()
        self.patient_selector = QComboBox()
        self.patient_selector.addItem("Select Patient")
        self.patient_selector.addItems([f"P{str(i).zfill(2)}" for i in range(1, 11)])
        self.patient_selector.currentIndexChanged.connect(self.update_sessions)
        dropdown_layout.addWidget(QLabel("Patient:"))
        dropdown_layout.addWidget(self.patient_selector)

        self.session_selector = QComboBox()
        self.session_selector.addItem("Select Session")
        self.session_selector.currentIndexChanged.connect(self.update_cameras)
        dropdown_layout.addWidget(QLabel("Session:"))
        dropdown_layout.addWidget(self.session_selector)

        self.camera_selector = QComboBox()
        self.camera_selector.addItem("Select Camera")
        self.camera_selector.currentIndexChanged.connect(self.update_segments)
        dropdown_layout.addWidget(QLabel("Camera:"))
        dropdown_layout.addWidget(self.camera_selector)

        self.segment_selector = QComboBox()
        self.segment_selector.addItem("Select Segment")
        self.segment_selector.currentIndexChanged.connect(self.final_selection_made)
        dropdown_layout.addWidget(QLabel("Segment:"))
        dropdown_layout.addWidget(self.segment_selector)

        layout.addLayout(dropdown_layout)

        self.load_video_button = QPushButton("Load")
        self.load_video_button.clicked.connect(self.load_all_data)
        layout.addWidget(self.load_video_button)

        self.video_label = QLabel()
        self.video_label.setMinimumHeight(480)  # Or 600, or whatever makes sense
        self.video_label.setStyleSheet("background-color: black;")  # Optional, improves appearance

        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        video_container = QHBoxLayout()
        video_container.addStretch()
        video_container.addWidget(self.video_label)
        video_container.addStretch()
        layout.addLayout(video_container)

        controls_layout = QHBoxLayout()
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.play_video)
        controls_layout.addWidget(self.play_button)

        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.pause_video)
        controls_layout.addWidget(self.pause_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_video)
        controls_layout.addWidget(self.stop_button)

        self.prev_frame_button = QPushButton("Previous")
        self.prev_frame_button.clicked.connect(self.step_backward)
        controls_layout.addWidget(self.prev_frame_button)

        self.next_frame_button = QPushButton("Next")
        self.next_frame_button.clicked.connect(self.step_forward)
        controls_layout.addWidget(self.next_frame_button)

        layout.addLayout(controls_layout)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setEnabled(False)
        self.slider.sliderMoved.connect(self.set_video_position)
        layout.addWidget(self.slider)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.plot_widget = pg.PlotWidget(axisItems={'bottom': TimeAxisItem(orientation='bottom')})
        self.vertical_line = pg.InfiniteLine(angle=90, pen=pg.mkPen('r', style=Qt.DashLine))
        self.plot_widget.addItem(self.vertical_line)
        layout.addWidget(self.plot_widget)

        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("Zoom (seconds):"))
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(1)
        self.zoom_slider.setMaximum(20)
        self.zoom_slider.setValue(self.zoom_window_sec)
        self.zoom_slider.setTickInterval(1)
        self.zoom_slider.setTickPosition(QSlider.TicksBelow)
        self.zoom_slider.setToolTip("Zoom: visible time window in seconds")
        self.zoom_slider.valueChanged.connect(self.update_zoom)
        zoom_layout.addWidget(self.zoom_slider)
        layout.addLayout(zoom_layout)

        self.signal_checkboxes_group = QGroupBox("Select Signal(s) to Plot")
        self.signal_checkboxes_layout = QGridLayout()
        self.signal_checkboxes_group.setLayout(self.signal_checkboxes_layout)
        layout.addWidget(self.signal_checkboxes_group)

        self.setLayout(layout)
        self.setWindowTitle("Video + IMU Viewer")
        self.setGeometry(100, 100, 800, 800)
        self.showFullScreen()

    def load_all_data(self):
        self.load_video()
        self.load_imu_data()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.showNormal()  # Exit fullscreen mode


    def step_forward(self):
        if self.current_frame_idx < len(self.frames) - 1:
            self.current_frame_idx += 1
            self.show_frame(self.current_frame_idx)

    def step_backward(self):
        if self.current_frame_idx > 0:
            self.current_frame_idx -= 1
            self.show_frame(self.current_frame_idx)

    def pause_video(self):
        if self.timer.isActive():
            self.timer.stop()

    def update_zoom(self, level):
        if self.time is None or len(self.time) == 0:
            return
        zoom_fraction = 1 / level
        self.zoom_window_sec = self.total_duration_sec * zoom_fraction

    def load_video(self):
        if (
            self.patient_selector.currentIndex() <= 0 or
            self.session_selector.currentIndex() <= 0 or
            self.camera_selector.currentIndex() <= 0 or
            self.segment_selector.currentIndex() <= 0
        ):
            print("⚠️ Please select all dropdowns before loading.")
            return

        camera = self.camera_selector.currentText()
        segment = self.segment_selector.currentText()
        camera_base_path = self.camera_paths.get(camera)

        if not camera_base_path:
            print("❌ Camera path not found.")
            return

        segment_path = os.path.join(camera_base_path, "Segments", segment)
        if not os.path.isdir(segment_path):
            print("❌ Segment folder not found.")
            return

        # Look for video file in the selected segment folder
        for fname in os.listdir(segment_path):
            if fname.lower().endswith((".mp4", ".mkv", ".avi", ".mov")):
                file_path = os.path.join(segment_path, fname)
                break
        else:
            print("❌ No video file found in segment folder.")
            return

        print("🎥 Loading video from:", file_path)

        self.container = av.open(file_path)
        self.stream = self.container.streams.video[0]
        self.fps = float(self.stream.average_rate)

        estimated_frames = int(self.stream.duration * self.stream.time_base * self.fps) if self.stream.duration else 0
        self.frames = []

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(estimated_frames if estimated_frames > 0 else 1000)

        for i, frame in enumerate(self.container.decode(self.stream)):
            self.frames.append(frame)
            if estimated_frames:
                self.progress_bar.setValue(min(i + 1, estimated_frames))
            elif i % 10 == 0:
                self.progress_bar.setValue(i + 1)
            QApplication.processEvents()

        self.progress_bar.setVisible(False)

        print(f"✅ Loaded {len(self.frames)} frames")
        self.slider.setRange(0, len(self.frames) - 1)
        self.slider.setEnabled(True)
        self.current_frame_idx = 0
        self.show_frame(0)


    def show_frame(self, idx):
        if 0 <= idx < len(self.frames):
            frame = self.frames[idx].to_ndarray(format='rgb24')

            # Get label dimensions and frame dimensions
            label_w = self.video_label.width()
            label_h = self.video_label.height()
            frame_h, frame_w = frame.shape[:2]

            # Compute scale factor to maintain aspect ratio
            scale = min(label_w / frame_w, label_h / frame_h)
            new_w = int(frame_w * scale)
            new_h = int(frame_h * scale)

            # Resize with aspect ratio preserved
            frame_resized = np.ascontiguousarray(cv2.resize(frame, (new_w, new_h)))

            # Create QImage and set it centered in QLabel
            qimg = QImage(
                frame_resized.data,
                frame_resized.shape[1],
                frame_resized.shape[0],
                frame_resized.strides[0],
                QImage.Format_RGB888,
            )
            pixmap = QPixmap.fromImage(qimg)

            # Center pixmap in QLabel
            self.video_label.setPixmap(pixmap)
            self.video_label.setAlignment(Qt.AlignCenter)

            self.slider.setValue(idx)
            self.update_imu_line(idx)


    def update_frame(self):
        self.current_frame_idx += 1
        if self.current_frame_idx >= len(self.frames):
            self.timer.stop()
        else:
            self.show_frame(self.current_frame_idx)

    def play_video(self):
        if self.frames:
            self.timer.start(int(1000 / self.fps))

    def stop_video(self):
        self.timer.stop()
        self.current_frame_idx = 0
        self.show_frame(0)

    def set_video_position(self, pos):
        self.current_frame_idx = pos
        self.show_frame(pos)

    def final_selection_made(self):
        # Just print or store the selected path — no loading here!
        if (
            self.patient_selector.currentIndex() <= 0 or
            self.session_selector.currentIndex() <= 0 or
            self.camera_selector.currentIndex() <= 0 or
            self.segment_selector.currentIndex() <= 0
        ):
            return

        patient = self.patient_selector.currentText()
        session = self.session_selector.currentText()
        camera = self.camera_selector.currentText()
        segment = self.segment_selector.currentText()

        camera_base_path = self.camera_paths.get(camera)
        if not camera_base_path:
            return

        segment_path = os.path.join(camera_base_path, "Segments", segment)
        print("📁 Final selection path ready:", segment_path)




    def load_imu_data(self):
        patient = self.patient_selector.currentText()
        session = self.session_selector.currentText()
        camera = self.camera_selector.currentText()
        segment = self.segment_selector.currentText()

        # Handle session prefix match (e.g. Session1_20250203)
        session_root = os.path.join(self.imu_base_path, patient)
        session_full = None
        for folder in os.listdir(session_root):
            if folder.startswith(session):
                session_full = folder
                break
        if not session_full:
            print("❌ Session folder not found in IMU path.")
            return

        imu_path = os.path.join(
            self.imu_base_path, patient, session_full, segment, "ViewerAssets", f"{camera}.csv"
        )

        if not os.path.isfile(imu_path):
            print("❌ IMU file not found:", imu_path)
            return

        print("📦 Loading IMU data from:", imu_path)
        self.imu_data = pd.read_csv(imu_path)
        self.time = np.arange(len(self.imu_data)) / self.fps

        self.signal_columns = list(self.imu_data.columns[1:])
        self.signals = {col: pd.to_numeric(self.imu_data[col], errors='coerce').to_numpy()
                        for col in self.signal_columns}

        for curve in self.signal_curves.values():
            self.plot_widget.removeItem(curve)
        self.signal_curves.clear()

        for col in self.signal_columns:
            curve = self.plot_widget.plot(pen=pg.intColor(len(self.signal_curves)))
            curve.setVisible(False)
            curve.setData(self.time, self.signals[col])
            self.signal_curves[col] = curve

        for i in reversed(range(self.signal_checkboxes_layout.count())):
            widget = self.signal_checkboxes_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        self.signal_checkboxes = {}
        for idx, col in enumerate(self.signal_columns):
            checkbox = QCheckBox(col)
            checkbox.stateChanged.connect(self.update_plot_from_checkboxes)
            row = idx // 9
            col_pos = idx % 9
            self.signal_checkboxes_layout.addWidget(checkbox, row, col_pos)
            self.signal_checkboxes[col] = checkbox

        self.signal_checkboxes[self.signal_columns[0]].setChecked(True)

        self.total_duration_sec = self.time[-1] if self.time is not None else 0
        self.zoom_slider.setMinimum(1)
        self.zoom_slider.setMaximum(20)
        self.zoom_slider.setValue(1)
        self.update_zoom(1)

    def update_plot_from_checkboxes(self):
        for col, checkbox in self.signal_checkboxes.items():
            if col in self.signal_curves:
                self.signal_curves[col].setVisible(checkbox.isChecked())

    def update_imu_line(self, frame_idx):
        if self.time is None or frame_idx >= len(self.time):
            return
        t = self.time[frame_idx]
        self.vertical_line.setPos(t)
        half_window = self.zoom_window_sec / 2
        self.plot_widget.setXRange(t - half_window, t + half_window, padding=0)

    def update_sessions(self):
        patient = self.patient_selector.currentText()
        base_path = self.base_path
        patient_path = os.path.join(base_path, patient)

        self.session_selector.clear()
        self.session_selector.addItem("Select Session")

        if os.path.isdir(patient_path):
            sessions = sorted([
                f for f in os.listdir(patient_path)
                if os.path.isdir(os.path.join(patient_path, f))
            ])
            self.session_selector.addItems(sessions)

    def update_cameras(self):
        patient = self.patient_selector.currentText()
        session = self.session_selector.currentText()
        base_path = "C:/Users/s4659771/Documents/MyTurn_Project/Data/Processed"
        session_path = os.path.join(base_path, patient, session)

        self.camera_selector.clear()
        self.camera_selector.addItem("Select Camera")  
        self.camera_paths = {}

        if os.path.isdir(session_path):
            video_root = os.path.join(session_path, "Video")
            for mode in ["CT", "VR", "FMA_and_VR"]:
                mode_path = os.path.join(video_root, mode)
                if os.path.isdir(mode_path):
                    for cam in sorted(os.listdir(mode_path)):
                        cam_path = os.path.join(mode_path, cam)
                        if os.path.isdir(cam_path):
                            self.camera_paths[cam] = cam_path
                            self.camera_selector.addItem(cam)



    def update_segments(self):
        camera = self.camera_selector.currentText()
        camera_path = self.camera_paths.get(camera, "")

        self.segment_selector.clear()
        self.segment_selector.addItem("Select Segment")  # optional placeholder

        if camera_path and os.path.isdir(camera_path):
            segments_root = os.path.join(camera_path, "Segments")
            if os.path.isdir(segments_root):
                segments = sorted([
                    f for f in os.listdir(segments_root)
                    if os.path.isdir(os.path.join(segments_root, f)) and "static" not in f.lower()
                ])
                self.segment_selector.addItems(segments)




if __name__ == "__main__":
    import cv2
    app = QApplication(sys.argv)
    viewer = VideoIMUPlayer()
    viewer.show()
    sys.exit(app.exec_())
