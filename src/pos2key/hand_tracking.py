# https://mediapipe.readthedocs.io/en/latest/solutions/hands.html

import cv2
import mediapipe as mp
import time
import math
import numpy as np

class HandController:
    def __init__(self, width=600, height=500, control_threshold=0.06):
        self.control_mode = False
        self.control_threshold = control_threshold

        self.window_titles = ["Hand Capture", "Virtual Buttons"]
        self.lane = "Center"
        self.action = "Neutral"
        self.lane_list = ("Left", "Center", "Right")
        self.action_list = ("Jump", "Slide", "Neutral")
        self.buttons_config = {"Left": [None, (255, 0, 0)], "Center": [None, (0, 255, 0)], "Right": [None, (0, 0, 255)], "Jump": [None, (255, 255, 0)], "Slide": [None, (255, 0, 255)], "Neutral": [None, None]}

        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        self.mp_drawing = mp.solutions.drawing_utils
        self.drawing_styles = mp.solutions.drawing_styles
        self.mp_hands = mp.solutions.hands

        self.hand = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.2,
            static_image_mode=False
        )

        self.finger_tips = [4, 8, 12, 16, 20] # thumb, index, middle, ring, pinky
        self.finger_mcps = [2, 5, 9, 13, 17]
        self.finger_ips = [3, 7, 11, 15, 19]
        self.wrist = 0
    
    def distance(self, x1, x2, y1, y2, z1=None, z2=None):
        if z1!=None and z2!=None:
            return math.sqrt((x1-x2)**2+(y1-y2)**2+(z1-z2)**2)
        return math.sqrt((x1-x2)**2+(y1-y2)**2)

    def check_control(self, landmark):
        """return True when making a pointer"""
        folded = 0
        for tip, mcp in zip(self.finger_ips[2:], self.finger_mcps[2:]):
            if self.distance(landmark[tip].x, landmark[mcp].x, landmark[tip].y, landmark[mcp].y) < self.control_threshold:
                folded+=1

        index_tip = landmark[self.finger_tips[1]]
        index_mcp = landmark[self.finger_mcps[1]]

        open_index_finger = (
            self.distance(index_tip.x, index_mcp.x, index_tip.y, index_mcp.y, landmark[tip].z, landmark[mcp].z) > self.control_threshold
        )

        # closed_thumb = (
        #     abs(landmark[self.finger_ip[0]].x - landmark[self.finger_ip[1]].x) < self.control_threshold and 
        #     abs(landmark[self.finger_ip[0]].y - landmark[self.finger_ip[1]].y) < self.control_threshold
        #     )

        # return folded==3 and open_index_finger
        return True
    
    def find_control_point(self, landmark, frame):
        cx, cy = landmark[self.finger_tips[1]].x, landmark[self.finger_tips[1]].y 
        w, h = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        x, y = int(cx*w), int(cy*h)
        cv2.circle(frame, (x, y), 20, (255,0,255), -1)
        return cx, cy
    
    def draw_info(self, frame, text):
        cv2.putText(frame, text, (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    def draw_buttons(self, frame):
        w, h = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        overlay = frame.copy()

        btn_width = w // 3
        remainder = w % 3 
        widths = [btn_width, btn_width, btn_width]
        for i in range(remainder):
            widths[i] += 1 

        # Full height split: top (jump), middle (3 buttons), bottom (slide)
        top_height = h // 6
        bottom_height = h // 6
        center_height = h - top_height - bottom_height  # Exact middle height

        # Starting Y positions
        y_jump = 0
        y_center = top_height
        y_slide = h - bottom_height

        # === Jump (top full-width rectangle) ===
        jump_rect = (0, y_jump, w, y_center)
        self.buttons_config["Jump"][0] = jump_rect
        cv2.rectangle(overlay, (0, y_jump), (w, y_center), self.buttons_config["Jump"][1], -1)

        neutral_rect = (0, y_center, w, y_slide)
        self.buttons_config["Neutral"][0] = neutral_rect    # Not display on cam

        # === Slide (bottom full-width rectangle) ===
        slide_rect = (0, y_slide, w, h)
        self.buttons_config["Slide"][0] = slide_rect
        cv2.rectangle(overlay, (0, y_slide), (w, h), self.buttons_config["Slide"][1], -1)

        # === Left, Center, Right (middle row) ===
        x_offset = 0
        for i, name in enumerate(["Left", "Center", "Right"]):
            x1 = x_offset
            x2 = x_offset + widths[i]
            rect = (x1, y_center, x2, y_center + center_height)
            self.buttons_config[name][0] = rect
            cv2.rectangle(overlay, (x1, y_center), (x2, y_center + center_height), self.buttons_config[name][1], -1)
            x_offset = x2  # Next button starts exactly where this one ends

        alpha = 0.3
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        for name, config in self.buttons_config.items():
            if name == "Neutral":   # Ignore Neutral to be drawn
                continue
            else:
                (x1, y1, x2, y2) = config[0]
                color = config[1]
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                # Center text in button
                text_size = cv2.getTextSize(name, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
                text_x = x1 + (x2 - x1 - text_size[0]) // 2
                text_y = y1 + (y2 - y1 + text_size[1]) // 2
                cv2.putText(frame, name, (text_x, text_y),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

    def run(self):
        while True:
            success, frame = self.cap.read() # Frames in BGR
            if not success:
                break

            flipped_frame = cv2.flip(frame, 1)

            rgb_frame = cv2.cvtColor(flipped_frame, cv2.COLOR_BGR2RGB)
            result = self.hand.process(rgb_frame)

            hand_frame = flipped_frame.copy()
            button_frame = flipped_frame.copy()

            self.draw_buttons(button_frame)

            if result.multi_hand_landmarks:
                hand_landmarks = result.multi_hand_landmarks[0]
                # print(hand_landmarks)
                self.mp_drawing.draw_landmarks(
                    hand_frame, 
                    hand_landmarks, 
                    self.mp_hands.HAND_CONNECTIONS, 
                    self.drawing_styles.get_default_hand_landmarks_style(),
                    self.drawing_styles.get_default_hand_connections_style()
                    )

                control_mode = self.check_control(hand_landmarks.landmark)
                mode_text = "Pointer (Control Mode)" if control_mode else "Open (Idle)"
                self.draw_info(hand_frame, mode_text)

                if control_mode:
                    cx, cy = self.find_control_point(hand_landmarks.landmark, hand_frame)
                    w, h = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    for name, config in self.buttons_config.items():
                        if cx > (config[0][0]/w) and cx < (config[0][2]/w) and name in self.lane_list:
                            self.lane = name
                        
                        if cy > (config[0][1]/h) and cy < (config[0][3]/h) and name in self.action_list:
                            self.action = name

                    match (self.lane, self.action):
                        case "Left", "Jump":
                            self.LEFT_JUMP()
                        case "Center", "Jump":
                            self.CENTRE_JUMP()
                        case "Right", "Jump":
                            self.RIGHT_JUMP()
                        case "Left", "Neutral":
                            self.LEFT_NEUTRAL()
                        case "Center", "Neutral":
                            self.CENTRE_NEUTRAL()
                        case "Right", "Neutral":
                            self.RIGHT_NEUTRAL()
                        case "Left", "Slide":
                            self.LEFT_ROLL()
                        case "Center", "Slide":
                            self.CENTRE_ROLL()
                        case "Right", "Slide":
                            self.RIGHT_ROLL()
                    time.sleep(0.1)

            cv2.imshow(self.window_titles[0], hand_frame)
            cv2.imshow(self.window_titles[1], button_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        self.cap.release()
        cv2.destroyAllWindows()
    
    def LEFT_JUMP(self):
        print("LEFT JUMP!")
        pass

    def CENTRE_JUMP(self):
        print("CENTRE JUMP!")
        pass

    def RIGHT_JUMP(self):
        print("RIGHT JUMP!")
        pass

    def LEFT_NEUTRAL(self):
        print("LEFT NEUTRAL!")
        pass

    def CENTRE_NEUTRAL(self):
        print("CENTRE NEUTRAL")
        pass

    def RIGHT_NEUTRAL(self):
        print("RIGHT NEUTRAL!")
        pass

    def LEFT_ROLL(self):
        print("LEFT ROLL!")
        pass

    def CENTRE_ROLL(self):
        print("CENTRE ROLL!")
        pass

    def RIGHT_ROLL(self):
        print("RIGHT ROLL!")
        pass



if __name__ == "__main__":
    controller = HandController()
    controller.run()