#!/usr/bin/env python
# coding: utf-8

# In[46]:


import cv2
import mediapipe as mp 
import util
import pyautogui
from pynput.mouse import Button, Controller
mouse = Controller()
import random


# In[47]:


import mediapipe as mp 

screen_width, screen_height = pyautogui.size()

mpHands = mp.solutions.hands
hands = mpHands.Hands(
    static_image_mode=False,
    model_complexity=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
    max_num_hands=1
)    


# In[48]:


def find_finger_tip(processed):
    if processed.multi_hand_landmarks:
        hand_landmarks = processed.multi_hand_landmarks[0]
        return hand_landmarks.landmark[mpHands.HandLandmark.INDEX_FINGER_TIP]

    return None
        


# In[49]:


# def move_mouse(index_finger_tip):
#     if index_finger_tip is not None:
#         x = int(index_finger_tip.x * screen_width)
#         y = int(index_finger_tip.y * screen_height)
#         pyautogui.moveTo(x, y)



# prev_x, prev_y = None, None
# smoothing = 0.7 

# def move_mouse(index_finger_tip):
#     global prev_x, prev_y
#     if index_finger_tip is None:
#         return
#     x = int(index_finger_tip.x * screen_width)
#     y = int(index_finger_tip.y * screen_height)
#     if prev_x is None:
#         prev_x, prev_y = x, y
    
#     x = int(prev_x * smoothing + x * (1 - smoothing))
#     y = int(prev_y * smoothing + y * (1 - smoothing))
#     pyautogui.moveTo(x, y)
#     prev_x, prev_y = x, y


prev_x, prev_y = None, None
smoothing = 0.7
def move_mouse(index_finger_tip, frame_width, frame_height):
    global prev_x, prev_y
    if index_finger_tip is None:
        return

    # مختصات انگشت در تصویر دوربین
    cam_x = index_finger_tip.x * frame_width
    cam_y = index_finger_tip.y * frame_height

    # مقیاس دادن به کل صفحه
    x = int(cam_x * screen_width / frame_width)
    y = int(cam_y * screen_height / frame_height)

    # نرم‌کردن حرکت
    if prev_x is None:
        prev_x, prev_y = x, y
    x = int(prev_x * smoothing + x * (1 - smoothing))
    y = int(prev_y * smoothing + y * (1 - smoothing))

    pyautogui.moveTo(x, y)
    prev_x, prev_y = x, y

  


# In[50]:


def is_left_click(landmarks_list, thumb_index_dist):
    return (
        util.get_angle(landmarks_list[5], landmarks_list[6], landmarks_list[8]) < 50 and 
        util.get_angle(landmarks_list[9], landmarks_list[10], landmarks_list[12]) > 90 and 
        thumb_index_dist > 70
    )

def is_right_click(landmarks_list, thumb_index_dist):
    return (
        util.get_angle(landmarks_list[5], landmarks_list[6], landmarks_list[8]) > 90 and 
        util.get_angle(landmarks_list[9], landmarks_list[10], landmarks_list[12]) < 50 and 
        thumb_index_dist > 50
    )

def is_double_click(landmarks_list, thumb_index_dist):
    return (
        util.get_angle(landmarks_list[5], landmarks_list[6], landmarks_list[8]) < 50 and 
        util.get_angle(landmarks_list[9], landmarks_list[10], landmarks_list[12]) < 50 and 
        thumb_index_dist > 50
    )    

def is_screenshot(landmarks_list, thumb_index_dist):
    return (
        util.get_angle(landmarks_list[5], landmarks_list[6], landmarks_list[8]) < 50 and 
        util.get_angle(landmarks_list[9], landmarks_list[10], landmarks_list[12]) < 50 and 
        util.get_angle(landmarks_list[13], landmarks_list[14], landmarks_list[16]) < 50 and
        util.get_angle(landmarks_list[17], landmarks_list[18], landmarks_list[20]) < 50 and
        thumb_index_dist < 50
    )


# In[51]:


#scroll
prev_initial_pos  = False  

def is_initial_position(landmarks_list, thumb_index_dist):
    # انگشت شصت، اشاره و وسط باز باشن
    thumb_open = thumb_index_dist > 50
    index_open = util.get_angle(landmarks_list[5], landmarks_list[6], landmarks_list[8]) > 90
    middle_open = util.get_angle(landmarks_list[9], landmarks_list[10], landmarks_list[12]) > 90
    
    # حلقه و کوچک بسته باشن
    ring_closed = util.get_angle(landmarks_list[13], landmarks_list[14], landmarks_list[16]) < 50
    pinky_closed = util.get_angle(landmarks_list[17], landmarks_list[18], landmarks_list[20]) < 50
    
    return thumb_open and index_open and middle_open and ring_closed and pinky_closed

def check_and_perform_scroll(frame, landmarks_list, thumb_index_dist):
    global prev_initial_pos 
    if len(landmarks_list) < 21:
        return

    initial_pos = is_initial_position(landmarks_list, thumb_index_dist)
    
    # وقتی از حالت اولیه به حالتی رفت که حلقه یا کوچک باز بشه → اسکرول کن
    if prev_initial_pos  and not initial_pos:
        pyautogui.scroll(-300)
        cv2.putText(frame, "Scroll performed", (50, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    prev_initial_pos  = initial_pos










# In[52]:


#drag and drop
from pynput.mouse import Button, Controller
mouse = Controller()

dragging = False 

def check_and_perform_drag(frame, landmarks_list, thumb_index_tip_dist, index_finger_tip):
    """
    اگر نوک انگشت شصت و اشاره نزدیک باشند و
    انگشت‌های وسط، حلقه و کوچک صاف باشند → شروع Drag
    اگر از هم دور شوند → Drop
    """
    global dragging

    #آستانه نزدیکی انگشت‌ها
    DRAG_THRESHOLD = 20
    ANGLE_THRESHOLD = 160  # زاویه‌ای که تقریبا صاف بودن انگشت را نشان می‌دهد

    # بررسی صاف بودن انگشت وسط، حلقه و کوچک
    middle_straight = util.get_angle(landmarks_list[9], landmarks_list[10], landmarks_list[12]) > ANGLE_THRESHOLD
    ring_straight   = util.get_angle(landmarks_list[13], landmarks_list[14], landmarks_list[16]) > ANGLE_THRESHOLD
    pinky_straight  = util.get_angle(landmarks_list[17], landmarks_list[18], landmarks_list[20]) > ANGLE_THRESHOLD

    if thumb_index_tip_dist < DRAG_THRESHOLD and middle_straight and ring_straight and pinky_straight:
        # فعال‌سازی Drag اگر قبلاً فعال نبوده
        if not dragging:
            mouse.press(Button.left)
            dragging = True
        # در حالت Drag ماوس را حرکت بده
        move_mouse(index_finger_tip, frame.shape[1], frame.shape[0])
        cv2.putText(frame, "Dragging...", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

    elif dragging:
        # پایان Drag → Drop
        mouse.release(Button.left)
        dragging = False
        cv2.putText(frame, "Dropped", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)


# In[53]:


def detect_gestures(frame, landmarks_list, processed):
    if len(landmarks_list) >= 21 :

        index_finger_tip = find_finger_tip(processed)
        thumb_index_dist = util.get_distance([landmarks_list[4], landmarks_list[5]])
        thumb_index_tip_dist=util.get_distance([landmarks_list[4], landmarks_list[8]])
        
        #scroll
        check_and_perform_scroll(frame, landmarks_list, thumb_index_dist)


        #drag and drop
        check_and_perform_drag(frame, landmarks_list, thumb_index_tip_dist, index_finger_tip)
        

        #move mouse
        if thumb_index_dist < 50 and util.get_angle(landmarks_list[5], landmarks_list[6], landmarks_list[8]) > 90:
            move_mouse(index_finger_tip, frame.shape[1], frame.shape[0])


        #left click 
        elif is_left_click(landmarks_list, thumb_index_dist):
            mouse.press(Button.left)
            mouse.release(Button.left)
            cv2.putText(frame, "left click", (50,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

        #right click
        elif  is_right_click(landmarks_list, thumb_index_dist):
            mouse.press(Button.right)
            mouse.release(Button.right)
            cv2.putText(frame, "right click", (50,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
        #double click 
        elif is_double_click(landmarks_list, thumb_index_dist):
            pyautogui.doubleClick()
            cv2.putText(frame, "double click", (50,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,0), 2)
            


        #screenshot
        elif is_screenshot(landmarks_list, thumb_index_dist):
            im1 = pyautogui.screenshot()
            label = random.randint(1, 1000)
            im1.save(f'my_screenshot_{label}.png')
            cv2.putText(frame, "screen shot taken", (50,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,0), 2)


# In[54]:


import cv2

def main():
    cap = cv2.VideoCapture(0)
    draw = mp.solutions.drawing_utils

    
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            
            if not ret:
                break
            

            frame = cv2.flip(frame, 1)
            frameRGB = cv2.cvtColor(frame , cv2.COLOR_BGR2RGB)
            processed = hands.process(frameRGB)

            landmarks_list = []

            if processed.multi_hand_landmarks:
                hand_landmarks = processed.multi_hand_landmarks[0]
                draw.draw_landmarks(frame , hand_landmarks , mpHands.HAND_CONNECTIONS)

                for lm in hand_landmarks.landmark:
                    landmarks_list.append((lm.x , lm.y))

                #print(landmarks_list)     


            detect_gestures(frame, landmarks_list, processed)
                       
                    

            cv2.imshow('Frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()

