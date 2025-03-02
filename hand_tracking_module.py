import cv2
import mediapipe as mp
from creating_rectangles import RectangleDrawer

rectangle_drawer = RectangleDrawer()

class HandTracker:
    def __init__(self, min_detection_confidence=0.1, min_tracking_confidence=0.5):
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            min_detection_confidence=self.min_detection_confidence, 
            min_tracking_confidence=self.min_tracking_confidence
        )


    # Inside HandTracker class
    def check_inside_rectangles(self, landmarks, rectangle_drawer):
        for idx, hand_landmarks in enumerate(landmarks):
            for landmark in hand_landmarks.landmark:
                x, y = int(landmark.x * 1280), int(landmark.y * 720)
                for p_idx, polygon in enumerate(rectangle_drawer.completed_polygons):
                    top_left, top_right, bottom_right, bottom_left = polygon
                    x1, y1 = top_left
                    x2, y2 = bottom_right
                    
                    if x1 < x < x2 and y1 < y < y2 and rectangle_drawer.show_green_overlay is False:
                        rectangle_drawer.set_hand_inside_flag(p_idx, True)
                        return
                    else:
                        rectangle_drawer.set_hand_inside_flag(p_idx, False)


    def process_frame(self, frame, rectangle_drawer_instance):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_image)
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS
                )
            self.check_inside_rectangles(results.multi_hand_landmarks, rectangle_drawer_instance)
        return frame


    def run(self):
        cap = cv2.VideoCapture(0)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Failed to fetch frame")
                continue

            annotated_frame = self.process_frame(frame)

            cv2.imshow('Hand Tracking', annotated_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break


        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    hand_tracker = HandTracker()
    hand_tracker.run()