import cv2
import mediapipe as mp
import pyautogui
import screen_brightness_control as sbc
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume_ctrl = cast(interface, POINTER(IAudioEndpointVolume))

def volume_up():
    current = volume_ctrl.GetMasterVolumeLevelScalar()
    volume_ctrl.SetMasterVolumeLevelScalar(min(current + 0.1, 1.0), None)

def volume_down():
    current = volume_ctrl.GetMasterVolumeLevelScalar()
    new_volume = max(current - 0.1, 0.0)
    volume_ctrl.SetMasterVolumeLevelScalar(new_volume, None)
    print (f"Volume down: {int(new_volume * 100)}")

def toggle_mute():
    is_muted = volume_ctrl.GetMute()
    volume_ctrl.SetMute(not is_muted, None)

def mute():
    toggle_mute()

def brightness_down():
    current = sbc.get_brightness(display=0)
    # sbc.get_brightness returns a list, get the first value
    if isinstance(current, list):
        current = current[0]
    new_brightness = max(current - 10, 0)
    sbc.set_brightness(new_brightness, display=0)
    print(f"Brightness down: {new_brightness}")

def brightness_up():
    current = sbc.get_brightness(display=0)
    # sbc.get_brightness returns a list, get the first value
    if isinstance(current, list):
        current = current[0]
    new_brightness = min(current + 10, 100)
    sbc.set_brightness(new_brightness, display=0)
    print(f"Brightness up: {new_brightness}")


mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils


hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7) 
cap = cv2.VideoCapture(0)

def is_thumb_up(landmarks):
    thumb_tip = landmarks[4]
    thumb_mcp = landmarks[2]
    wrist = landmarks[0]

    # Thumbs up if thumb_tip is significantly above wrist (y-axis)
    return thumb_tip.y < thumb_mcp.y and thumb_tip.y < wrist.y



def get_finger_states(hand_landmarks):
    finger_states = []

    # Tip landmarks for fingers: Thumb(4), Index(8), Middle(12), Ring(16), Pinky(20)
    tips_ids = [4, 8, 12, 16, 20]

    # Wrist landmark
    wrist_y = hand_landmarks.landmark[0].y

    # Thumb: compare x-coordinates
    if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x:
        finger_states.append(1)
    else:
        finger_states.append(0)

    # Other fingers: compare tip.y and pip.y
    for id in range(1, 5):
        if hand_landmarks.landmark[tips_ids[id]].y < hand_landmarks.landmark[tips_ids[id] - 2].y:
            finger_states.append(1)
        else:
            finger_states.append(0)

    return finger_states  # [thumb, index, middle, ring, pinky]

while True:
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)

    if result.multi_hand_landmarks:
        for handLms in result.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, handLms, mp_hands.HAND_CONNECTIONS)

        # Removed get_thumb_state usage since it's not defined.
        # Gesture detection is handled by get_finger_states below.

        finger_states = get_finger_states(handLms)
        if finger_states == [1, 0, 0, 0, 0]:  # Thumbs Up
            print("Gesture: Thumbs Up - Volume Up")
            volume_up()
                
        elif finger_states == [0, 0, 0, 0, 1]:  # Thumbs Down
            print("Gesture: Thumbs Down - Volume Down")
            volume_down()

        elif finger_states == [0, 1, 1, 0, 0]:  # Peace Sign
            print("Gesture: Peace - unmute")
            volume_ctrl.SetMute(0, None) 
        
        elif finger_states == [0, 1, 1, 1, 0]:  # Three Fingers (Unmute)
            print("Gesture: Three Fingers - mute")
            mute()  # Unmute system audio

        elif finger_states == [0, 0, 0, 0, 0]:  # Fist
            print("Gesture: Fist - Brightness Down")
            brightness_down()
       
        elif finger_states == [1, 1, 1, 1, 1]:  # Open Palm
            print("Gesture: Palm - Brightness Up")
            brightness_up()

        else:
                cv2.putText(frame, f"Fingers: {finger_states}", (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("Gesture Control", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
