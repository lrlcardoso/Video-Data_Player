# Video IMU Viewer

A PyQt5-based desktop application for synchronized visualization of video frames and IMU signal data. Built for researchers and engineers analyzing movement data captured from rehabilitation or biomechanics sessions.

---

## 🎯 Features

- Load and play video recordings from segmented experimental trials
- Overlay synchronized IMU signals (from CSV files) in an interactive plot
- Zoom in/out on time-aligned signals
- Navigate frame-by-frame or play continuously
- Select and toggle multiple IMU channels dynamically

---

## ⚙️ Requirements

- Python 3.8+
- PyQt5
- PyQtGraph
- OpenCV
- NumPy
- Pandas
- PyAV

Install dependencies via pip:
```bash
python -m pip install -r requirements.txt
```

---

## 🚀 Usage

```bash
python gui.py
```

### Workflow
1. Select **Patient**, **Session**, **Camera**, and **Segment** from the dropdowns
2. Click **Load** to populate video frames and IMU signal plots
3. Use playback buttons or the slider to navigate
4. Select IMU signal channels to visualize

---

## 🧪 Use Cases
- Neurorehabilitation trials
- Motion capture analysis
- Biomechanical signal inspection
- Synchronization verification of sensor data

---

## 📦 License
MIT License  
© 2025 Lucas Cardoso
