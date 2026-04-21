import cv2
import numpy as np
import HandTrackingModule as htm
import time
import pyautogui
import os
import math
import threading
from flask import Flask, render_template, Response, jsonify

# Silence TensorFlow logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Disable PyAutoGUI Failsafe
pyautogui.FAILSAFE = False

app = Flask(__name__)

class SterileCockpit:
    def __init__(self):
        self.wCam, self.hCam = 640, 480
        self.frameR = 100
        self.smoothening = 5
        self.pTime = 0
        self.plocX, self.plocY = 0, 0
        self.clocX, self.clocY = 0, 0
        
        self.is_clicked = False
        self.is_left_dragging = False
        self.is_right_dragging = False
        self.prev_zoom_dist = 0
        self.prev_scroll_y = 0
        self.voice_trigger_time = 0
        
        self.is_locked = False
        self.lock_trigger_time = 0
        self.is_fist_held = False
        
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, self.wCam)
        self.cap.set(4, self.hCam)
        
        self.detector = htm.handDetector(maxHands=2)
        self.wScr, self.hScr = pyautogui.size()
        
        self.current_mode = "INITIALIZING"
        self.fps = 0
        self.lock = threading.Lock()

    def get_frame(self):
        while True:
            success, img = self.cap.read()
            if not success:
                continue

            img = cv2.flip(img, 1)
            img = self.detector.findHands(img)
            lmList1, bbox1 = self.detector.findPosition(img, handNo=0, draw=False)

            mode_text = "READY"
            
            if lmList1:
                x1, y1 = lmList1[8][1:]     # Index finger tip
                x2, y2 = lmList1[12][1:]    # Middle finger tip
                fingers = self.detector.fingersUp()

                cv2.rectangle(img, (self.frameR, self.frameR),
                              (self.wCam - self.frameR, self.hCam - self.frameR),
                              (255, 0, 255), 2)

                # 🔒 LOCK / UNLOCK TOGGLE
                if fingers == [0, 0, 0, 0, 0]:
                    if not self.is_fist_held:
                        self.is_fist_held = True
                        self.lock_trigger_time = time.time()
                    elif time.time() - self.lock_trigger_time > 1.5:
                        self.is_locked = not self.is_locked
                        self.lock_trigger_time = time.time() + 2
                        if self.is_locked:
                            if self.is_left_dragging: pyautogui.mouseUp(button='left'); self.is_left_dragging = False
                            if self.is_right_dragging: pyautogui.mouseUp(button='right'); self.is_right_dragging = False
                else:
                    self.is_fist_held = False

                if self.is_locked:
                    mode_text = "LOCKED"
                    cv2.putText(img, "SYSTEM LOCKED", (150, 50), cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 255), 3)
                else:
                    # Logic branch
                    if fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 1:
                        mode_text = "VOICE TYPING"
                        if time.time() - self.voice_trigger_time > 2.0:
                            pyautogui.hotkey('win', 'h')
                            self.voice_trigger_time = time.time()
                            
                    elif fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 0:
                        mode_text = "SCROLL MODE"
                        if self.prev_scroll_y != 0:
                            dy = self.prev_scroll_y - y1
                            if abs(dy) > 5:
                                pyautogui.scroll(int(dy * 4))
                                self.prev_scroll_y = y1
                        else: self.prev_scroll_y = y1
                    
                    else:
                        self.prev_scroll_y = 0
                        length_pinch_index, img, pinchInfo = self.detector.findDistance(4, 8, img, draw=False)
                        length_pinch_middle, img, pinchInfoRight = self.detector.findDistance(4, 12, img, draw=False)
                        
                        if length_pinch_index < 40 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
                            mode_text = "MOVE SLICE"
                            if not self.is_left_dragging:
                                pyautogui.mouseDown(button='left')
                                self.is_left_dragging = True
                            self.move_mouse(x1, y1)
                            cv2.circle(img, (int(x1), int(y1)), 15, (0, 255, 255), cv2.FILLED)
                        
                        elif length_pinch_middle < 40 and fingers[1] == 0 and fingers[3] == 0 and fingers[4] == 0:
                            mode_text = "ROTATE 3D"
                            if not self.is_right_dragging:
                                pyautogui.mouseDown(button='right')
                                self.is_right_dragging = True
                            self.move_mouse(x2, y2)
                            cv2.circle(img, (int(x2), int(y2)), 15, (0, 165, 255), cv2.FILLED)

                        else:
                            if self.is_left_dragging: pyautogui.mouseUp(button='left'); self.is_left_dragging = False
                            if self.is_right_dragging: pyautogui.mouseUp(button='right'); self.is_right_dragging = False

                            if fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
                                mode_text = "CURSOR MOVE"
                                self.move_mouse(x1, y1)
                                cv2.circle(img, (int(x1), int(y1)), 15, (255, 0, 255), cv2.FILLED)
                                self.is_clicked = False

                            elif fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0:
                                length, img, lineInfo = self.detector.findDistance(8, 12, img, draw=False)
                                if length < 40:
                                    mode_text = "CLICK"
                                    if not self.is_clicked:
                                        try: pyautogui.click()
                                        except: pass
                                        self.is_clicked = True
                                    cv2.circle(img, (lineInfo[4], lineInfo[5]), 15, (0, 255, 0), cv2.FILLED)
                                else: self.is_clicked = False

                # ZOOM MODE
                if not self.is_locked and self.detector.results and self.detector.results.multi_hand_landmarks and len(self.detector.results.multi_hand_landmarks) == 2:
                    lmList2, bbox2 = self.detector.findPosition(img, handNo=1, draw=False)
                    if lmList1 and lmList2:
                        mode_text = "ZOOM MODE"
                        x_h1, y_h1 = lmList1[0][1], lmList1[0][2]
                        x_h2, y_h2 = lmList2[0][1], lmList2[0][2]
                        dist_hands = math.hypot(x_h2 - x_h1, y_h2 - y_h1)
                        if self.prev_zoom_dist != 0:
                            diff = dist_hands - self.prev_zoom_dist
                            if diff > 15: pyautogui.hotkey('ctrl', '+'); self.prev_zoom_dist = dist_hands
                            elif diff < -15: pyautogui.hotkey('ctrl', '-'); self.prev_zoom_dist = dist_hands
                        else: self.prev_zoom_dist = dist_hands
                else: self.prev_zoom_dist = 0

            self.current_mode = mode_text
            
            cTime = time.time()
            self.fps = 1 / (cTime - self.pTime) if (cTime - self.pTime) > 0 else 0
            self.pTime = cTime

            ret, buffer = cv2.imencode('.jpg', img)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    def move_mouse(self, x, y):
        x_clamped = np.clip(x, self.frameR, self.wCam - self.frameR)
        y_clamped = np.clip(y, self.frameR, self.hCam - self.frameR)
        x3 = np.interp(x_clamped, (self.frameR, self.wCam - self.frameR), (0, self.wScr))
        y3 = np.interp(y_clamped, (self.frameR, self.hCam - self.frameR), (0, self.hScr))
        
        self.clocX = self.plocX + (x3 - self.plocX) / self.smoothening
        self.clocY = self.plocY + (y3 - self.plocY) / self.smoothening
        
        if abs(self.clocX - self.plocX) > 2 or abs(self.clocY - self.plocY) > 2:
            try:
                pyautogui.moveTo(int(np.clip(self.clocX, 0, self.wScr - 1)), 
                                  int(np.clip(self.clocY, 0, self.hScr - 1)))
            except: pass
            self.plocX, self.plocY = self.clocX, self.clocY

cockpit = SterileCockpit()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/dashboard')
def dashboard():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(cockpit.get_frame(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
def status():
    return jsonify({
        'mode': cockpit.current_mode,
        'fps': int(cockpit.fps),
        'locked': cockpit.is_locked
    })

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
