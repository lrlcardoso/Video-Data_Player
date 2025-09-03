# RehabTrack Workflow – Video–IMU Viewer

This is an optional module of the [RehabTrack Workflow](https://github.com/lrlcardoso/RehabTrack_Workflow): a modular pipeline for **tracking and analysing physiotherapy movements**, using video and IMU data.  
This PyQt5-based desktop app enables synchronized, interactive visualisation of **video recordings and IMU signals** from rehabilitation sessions.

---

## 📌 Overview

This module provides:
- **Patient/session/segment navigation** through dropdowns
- **Synchronized playback** of video frames and IMU data
- **Multi-signal display** from processed CSV files
- **Zoomable time plots** and frame-level inspection
- **Optional combined-camera mode** with signal overlay

**Inputs:**
- Segmented video files from the VideoDataProcessing stage
- IMU and movement signal CSVs (e.g. from GrossMovDetector stage)

**Outputs:**
- Visualisation only (no files are saved by default)

---

## 📂 Repository Structure

```
VideoIMUViewer/
├── gui.py               # PyQt5 GUI application
├── requirements.txt     # Python dependencies
└── README.md
```

---

## 🛠 Installation

```bash
git clone https://github.com/yourusername/VideoIMUViewer.git
cd VideoIMUViewer
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## 🚀 Usage

Launch the application:
```bash
python gui.py
```

### Workflow:
1. Select **Patient**, **Session**, **Camera**, and **Segment**
2. Click **Load** to view synchronized video and signal plots
3. Use playback controls or the slider to navigate frames
4. Toggle IMU and use-signal channels to overlay on the timeline

---

## 📝 License

Code: [MIT License](LICENSE)  

---

## 🤝 Acknowledgments

- PyQt5, PyQtGraph  
- OpenCV
