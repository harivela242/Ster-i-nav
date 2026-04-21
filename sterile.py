import cv2
import numpy as np
import HandTrackingModule as htm
import time
import pyautogui
import os
import math

# Silence TensorFlow logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Disable PyAutoGUI Failsafe
pyautogui.FAILSAFE = False

# Camera settings
wCam, hCam = 640, 480
frameR = 100
smoothening = 5 # Reduced slightly for better responsiveness

pTime = 0
plocX, plocY = 0, 0
clocX, clocY = 0, 0

# State trackers for advanced modes
is_clicked = False # State to prevent rapid-fire clicking
is_left_dragging = False # For Target Slice (Left Drag)
is_right_dragging = False # For Rotate 3D (Right Drag)
prev_zoom_dist = 0
prev_scroll_y = 0
voice_trigger_time = 0

# Lock system state
is_locked = False
lock_trigger_time = 0
is_fist_held = False

cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)

detector = htm.handDetector(maxHands=2) # Changed to 2 for Zoom mode tracking
wScr, hScr = pyautogui.size()

# Set the window to be always on top
cv2.namedWindow("Virtual Mouse")
cv2.setWindowProperty("Virtual Mouse", cv2.WND_PROP_TOPMOST, 1)

while True:
    success, img = cap.read()
    if not success:
        continue

    # ✅ Mirror camera image
    img = cv2.flip(img, 1)

    img = detector.findHands(img)
    
    # Process primary hand for all single-hand gestures
    lmList1, bbox1 = detector.findPosition(img, handNo=0, draw=False)

    if lmList1:
        x1, y1 = lmList1[8][1:]     # Index finger tip
        x2, y2 = lmList1[12][1:]    # Middle finger tip

        fingers = detector.fingersUp()

        cv2.rectangle(img, (frameR, frameR),
                      (wCam - frameR, hCam - frameR),
                      (255, 0, 255), 2)

        mode_text = ""

        # 🔒 LOCK / UNLOCK TOGGLE (Closed Fist [0, 0, 0, 0, 0])
        if fingers == [0, 0, 0, 0, 0]:
            if not is_fist_held:
                is_fist_held = True
                lock_trigger_time = time.time()
            elif time.time() - lock_trigger_time > 1.5:
                # Toggle the lock state
                is_locked = not is_locked
                lock_trigger_time = time.time() + 2 # Cooldown to avoid rapid flapping
                
                # Safety cleanup on lock
                if is_locked:
                    if is_left_dragging:
                        pyautogui.mouseUp(button='left')
                        is_left_dragging = False
                    if is_right_dragging:
                        pyautogui.mouseUp(button='right')
                        is_right_dragging = False
        else:
            is_fist_held = False

        if is_locked:
            cv2.putText(img, "SYSTEM LOCKED", (150, 50), cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 255), 3)
            cv2.putText(img, "(Hold Fist to Unlock)", (150, 90), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)
        else:
            # 🎤 VOICE TYPING MODE (Win + H) - Pinky finger ONLY up (Ignore thumb flakiness)
            if fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 1:
                mode_text = "VOICE TYPING"
                if time.time() - voice_trigger_time > 2.0: # 2 sec cooldown
                    pyautogui.hotkey('win', 'h')
                    voice_trigger_time = time.time()
                    
            # 📜 SCROLL MODE - Index, Middle, Ring up
            elif fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 0:
                mode_text = "SCROLL MODE"
                if prev_scroll_y != 0:
                    dy = prev_scroll_y - y1
                    if abs(dy) > 5:  # Deadzone for scroll
                        # Map the raw hand Y movement to scroll amount. Multiply for speed on Windows.
                        pyautogui.scroll(int(dy * 4)) 
                        prev_scroll_y = y1
                else:
                    prev_scroll_y = y1
            
            else:
                prev_scroll_y = 0  # Reset scroll baseline when leaving mode

                # 🖱️ PINCH MEASUREMENTS
                # Length for Thumb (4) and Index (8) -> Left Click Drag (Move Slice)
                length_pinch_index, img, pinchInfo = detector.findDistance(4, 8, img, draw=False)
                # Length for Thumb (4) and Middle (12) -> Right Click Drag (Rotate 3D)
                length_pinch_middle, img, pinchInfoRight = detector.findDistance(4, 12, img, draw=False)
                
                # Check Left-Click Drag (Index Pinch & Middle Down)
                if length_pinch_index < 40 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
                    mode_text = "MOVE SLICE (LEFT DRAG)"
                    if not is_left_dragging:
                        pyautogui.mouseDown(button='left')
                        is_left_dragging = True
                    
                    # Core pointer drag movement
                    x1_clamped = np.clip(x1, frameR, wCam - frameR)
                    y1_clamped = np.clip(y1, frameR, hCam - frameR)
                    x3 = np.interp(x1_clamped, (frameR, wCam - frameR), (0, wScr))
                    y3 = np.interp(y1_clamped, (frameR, hCam - frameR), (0, hScr))
                    
                    clocX = plocX + (x3 - plocX) / smoothening
                    clocY = plocY + (y3 - plocY) / smoothening
                    if abs(clocX - plocX) > 2 or abs(clocY - plocY) > 2:
                        safe_x = int(np.clip(clocX, 0, wScr - 1))
                        safe_y = int(np.clip(clocY, 0, hScr - 1))
                        pyautogui.moveTo(safe_x, safe_y)
                        plocX, plocY = clocX, clocY
                    cv2.circle(img, (int(x1), int(y1)), 15, (0, 255, 255), cv2.FILLED)
                
                # Check Right-Click Drag (Middle Pinch & Index Down)
                elif length_pinch_middle < 40 and fingers[1] == 0 and fingers[3] == 0 and fingers[4] == 0:
                    mode_text = "ROTATE 3D (RIGHT DRAG)"
                    if not is_right_dragging:
                        pyautogui.mouseDown(button='right')
                        is_right_dragging = True
                    
                    # Pointer drag movement driven by Middle finger tip location
                    x_mid_clamp = np.clip(x2, frameR, wCam - frameR)
                    y_mid_clamp = np.clip(y2, frameR, hCam - frameR)
                    x3 = np.interp(x_mid_clamp, (frameR, wCam - frameR), (0, wScr))
                    y3 = np.interp(y_mid_clamp, (frameR, hCam - frameR), (0, hScr))
                    
                    clocX = plocX + (x3 - plocX) / smoothening
                    clocY = plocY + (y3 - plocY) / smoothening
                    if abs(clocX - plocX) > 2 or abs(clocY - plocY) > 2:
                        safe_x = int(np.clip(clocX, 0, wScr - 1))
                        safe_y = int(np.clip(clocY, 0, hScr - 1))
                        pyautogui.moveTo(safe_x, safe_y)
                        plocX, plocY = clocX, clocY
                    cv2.circle(img, (int(x2), int(y2)), 15, (0, 165, 255), cv2.FILLED) # Orange dot

                else:
                    # Release hooks
                    if is_left_dragging:
                        try:
                            pyautogui.mouseUp(button='left')
                        except Exception:
                            pass
                        is_left_dragging = False
                        
                    if is_right_dragging:
                        try:
                            pyautogui.mouseUp(button='right')
                        except Exception:
                            pass
                        is_right_dragging = False

                    # 🖱️ NORMAL MOVE MODE (index finger only)
                    if fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
                        mode_text = "MOVE"
                        # Clamp values (prevents tracking outside our active box)
                        x1_clamped = np.clip(x1, frameR, wCam - frameR)
                        y1_clamped = np.clip(y1, frameR, hCam - frameR)

                        x3 = np.interp(x1_clamped, (frameR, wCam - frameR), (0, wScr))
                        y3 = np.interp(y1_clamped, (frameR, hCam - frameR), (0, hScr))

                        # Exponential smoothing
                        clocX = plocX + (x3 - plocX) / smoothening
                        clocY = plocY + (y3 - plocY) / smoothening

                        # Prevent jitter when holding hand visually steady
                        if abs(clocX - plocX) > 2 or abs(clocY - plocY) > 2:
                            safe_x = int(np.clip(clocX, 0, wScr - 1))
                            safe_y = int(np.clip(clocY, 0, hScr - 1))
                            pyautogui.moveTo(safe_x, safe_y)
                            plocX, plocY = clocX, clocY

                        cv2.circle(img, (int(x1), int(y1)), 15, (255, 0, 255), cv2.FILLED)
                        is_clicked = False # Reset click state

                    # 🖱️ NORMAL CLICK MODE (index + middle finger)
                        
                    elif fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0:
                        length, img, lineInfo = detector.findDistance(8, 12, img, draw=False)
                        if length < 40:
                            mode_text = "CLICK"
                            if not is_clicked: # Debounce
                                try:
                                    pyautogui.click()
                                except Exception:
                                    pass
                                is_clicked = True
                            cv2.circle(img, (lineInfo[4], lineInfo[5]), 15, (0, 255, 0), cv2.FILLED)
                        else:
                            is_clicked = False
                            
            if mode_text:
                cv2.putText(img, mode_text, (150, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 200, 0), 2)

    # 🔎 ZOOM MODE (Two Hands)
    if not is_locked and detector.results and detector.results.multi_hand_landmarks and len(detector.results.multi_hand_landmarks) == 2:
        lmList2, bbox2 = detector.findPosition(img, handNo=1, draw=False)
        if lmList1 and lmList2:
            # Measure distance between wrists (lmList index 0)
            x_h1, y_h1 = lmList1[0][1], lmList1[0][2]
            x_h2, y_h2 = lmList2[0][1], lmList2[0][2]
            dist_hands = math.hypot(x_h2 - x_h1, y_h2 - y_h1)
            
            cv2.line(img, (x_h1, y_h1), (x_h2, y_h2), (0, 255, 255), 2)
            cv2.putText(img, "ZOOM MODE", (150, 100), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 255), 2)
            
            if prev_zoom_dist != 0:
                diff = dist_hands - prev_zoom_dist
                if diff > 15: # Expanding (Zoom In)
                    pyautogui.hotkey('ctrl', '+')
                    prev_zoom_dist = dist_hands
                elif diff < -15: # Contracting (Zoom Out)
                    pyautogui.hotkey('ctrl', '-')
                    prev_zoom_dist = dist_hands
            else:
                prev_zoom_dist = dist_hands
    else:
        prev_zoom_dist = 0

    # FPS display
    cTime = time.time()
    fps = 1 / (cTime - pTime) if (cTime - pTime) > 0 else 0
    pTime = cTime

    cv2.putText(img, f'FPS: {int(fps)}', (10, 30),
                cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)

    cv2.imshow("Virtual Mouse", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
