# 🏥 Sterile Cockpit: Gesture-Based Medical Controller

**Sterile Cockpit** is a touchless, gesture-controlled human-computer interface (HCI) tailored for sterile environments, such as surgical suites or dental clinics. It allows professionals to interact with 3D medical software, scroll through patient records, and navigate systems without breaking the sterile field.

![Sterile Cockpit Banner](https://img.shields.io/badge/Status-Beta-purple)
![License](https://img.shields.io/badge/License-MIT-green)
![Python](https://img.shields.io/badge/Python-3.8+-blue)

---

## 🌟 Key Features

- **Touchless Precision**: Control your mouse cursor using only hand movements.
- **Advanced Gestures**:
  - **Left Drag**: Specifically for manipulating 2D/3D slices.
  - **Right Drag**: Designed for 3D model rotation.
  - **Smooth Zooming**: Two-handed gesture for zooming in/out of imaging software.
  - **Natural Scrolling**: Smooth vertical scrolling with hand height.
- **Sterile Safety**: A built-in "Lock/Unlock" mechanism to prevent accidental inputs during procedures.
- **Web Dashboard**: A Flask-based web interface to monitor tracking in real-time.
- **Voice Integration**: Hands-free voice typing activation.

---

## 🚀 Getting Started

### 1. Prerequisites
Ensure you have **Python 3.8+** installed on your system.

### 2. Installation
Clone the repository and install the required libraries:

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/SterileCockpit.git
cd SterileCockpit

# Install dependencies
pip install -r requirements.txt
```

### 3. Usage

#### Run the Standalone Script (Desktop Mode)
Best for direct system control:
```bash
python sterile.py
```

#### Run the Web Dashboard
Best for remote monitoring or tablet view:
```bash
python app.py
```
*Access the dashboard at: `http://localhost:5000`*

—

## ✋ Gesture Guide

| Action | Gesture |
| :--- | :--- |
| **Move Cursor** | Point with Index Finger up |
| **Left Click** | Index + Middle Fingertips together |
| **Left Drag** | Pinch Thumb + Index (Middle down) |
| **Right Drag** | Pinch Thumb + Middle (Index down) |
| **Scroll** | Index, Middle, & Ring up (Move Hand Up/Down) |
| **Zoom** | Two-Handed (Wreist Distance) |
| **Voice Typing** | Pinky Finger ONLY up |
| **Lock/Unlock** | Hold a Closed Fist for 1.5 seconds |

---

## 🛠️ Built With

- [OpenCV](https://opencv.org/) - Computer vision processing.
- [MediaPipe](https://mediapipe.dev/) - Hand tracking and landmark detection.
- [PyAutoGUI](https://pyautogui.readthedocs.io/) - Cross-platform GUI automation.
- [Flask](https://flask.palletsprojects.com/) - Web framework for terminal interface.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*Developed for Table Clinics and Sterile Medical Environments.*
