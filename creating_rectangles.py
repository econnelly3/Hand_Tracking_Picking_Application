import cv2
import threading
import numpy as np
import json

class RectangleDrawer:
    def clear_polygons(self):
        self.completed_polygons.clear()
        self.show_green_overlay = False
        self.show_red_overlay = False
        self.next_rectangle_idx = 0
        self.triggered_indices = set()  # Add this new attribute
        self.completed_polygons = []
        self.is_hand_inside = []  # Initialize flags
        print("Cleared polygons")
        with open("polygon_coordinates.txt", "w") as f:
            f.write("")  # Write an empty string to clear the file


    def save_coordinates(self, filename="polygon_coordinates.txt"):
        with open(filename, "w") as f:
            json.dump(self.completed_polygons, f, indent=4)
    def load_coordinates(self, filename="polygon_coordinates.txt"):
        try:
            with open(filename, "r") as f:
                self.completed_polygons = json.load(f)
        except json.JSONDecodeError:
            print("JSON Decode Error: The file is either empty or not well-formatted")
            self.completed_polygons = []
        except FileNotFoundError:
            print("File not found. Initializing an empty list.")
            self.completed_polygons = []

    def __init__(self):
        self.points = []
        self.completed_polygons = []
        self.is_hand_inside = []  # Initialize flags
        self.next_rectangle_idx = 0
        self.triggered_indices = set()  # Add this new attribute
        self.show_green_overlay = False
        self.show_red_overlay = False
        self.cursor_pos = None
        try:
            self.load_coordinates()  # Load coordinates at the start
            for _ in self.completed_polygons:
                self.is_hand_inside.append(False)  # Initialize flags for the loaded polygons
        except FileNotFoundError:
            print("No saved polygons found.")
    def cancel(self):
        self.points.clear()  # This clears the points for the current incomplete polygon

    def mouse_move_event(self, event=None, x=None, y=None, flags=None, param=None):
        if event is None:  # This would be true when called from Flask
            self.cursor_pos = (x, y)
            return
        if event == cv2.EVENT_MOUSEMOVE:  # This would be true when called from OpenCV
            self.cursor_pos = (x, y)

    def click_event(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.points.append((x, y))
            if len(self.points) == 4:
                self.completed_polygons.append(self.points.copy())
                self.is_hand_inside.append(False)  # Add a flag for the new polygon
                self.points = []
                self.save_coordinates()  # Save to file each time you complete a polygon
    
    def turn_off_green_overlay(self):
        self.show_green_overlay = False

    def turn_off_red_overlay(self):
        self.show_red_overlay = False

    def finish_round(self):
        print("Finishi round")
        self.show_green_overlay = True
        self.next_rectangle_idx = 0
        self.triggered_indices.clear()
        threading.Timer(3.0, self.turn_off_green_overlay).start()
        
  

    def wrong_order(self):
        print("Wrong order")
        self.show_red_overlay = True
        threading.Timer(3.0, self.turn_off_red_overlay).start()


    def set_hand_inside_flag(self, index, value):
        if index == self.next_rectangle_idx and value == True:
            self.triggered_indices.add(index)  # Mark this rectangle as triggered
            self.next_rectangle_idx += 1  # Move on to the next rectangle
            if self.next_rectangle_idx >= len(self.completed_polygons):
                self.finish_round()
        else:
            if value == True and index not in self.triggered_indices:
                self.wrong_order()  # Call the function that sets show_red_overlay = True
            elif index not in self.triggered_indices:
                self.is_hand_inside[index] = False
    def add_point(self, x, y):
        self.points.append((x, y))
        if len(self.points) == 4:
            self.completed_polygons.append(self.points.copy())
            self.is_hand_inside.append(False)  # Add a flag for the new polygon
            self.points = []
            self.save_coordinates()  # Save to file each time you complete a polygon

    def draw_polygon(self, frame):
        # Draw completed polygons
        for idx, polygon in enumerate(self.completed_polygons):
            if idx == self.next_rectangle_idx:
                color = (255, 0, 0)  # Blue for the next expected rectangle
            elif idx in self.triggered_indices:
                color = (0, 255, 0)  # Green if already triggered
            else:
                color = (0, 0, 255)  # Red otherwise

            pts = np.array([polygon], np.int32)
            pts = pts.reshape((-1, 1, 2))
            
            overlay = frame.copy()
            
            # Filling the polygon on the overlay
            cv2.fillPoly(overlay, [pts], color)
            
            # Alpha blending overlay and frame
            alpha = 0.3  # Transparency factor
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
            
            # Drawing the outline
            cv2.line(frame, polygon[0], polygon[1], color, 2)
            cv2.line(frame, polygon[1], polygon[2], color, 2)
            cv2.line(frame, polygon[2], polygon[3], color, 2)
            cv2.line(frame, polygon[3], polygon[0], color, 2)
            
            avg_x = int((polygon[0][0] + polygon[2][0]) / 2)
            avg_y = int((polygon[0][1] + polygon[2][1]) / 2)
            
            cv2.putText(frame, str(idx + 1), (avg_x, avg_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        n = len(self.points)

        for i in range(n - 1):
            cv2.line(frame, self.points[i], self.points[i + 1], (0, 0, 255), 2)
            if self.points and self.cursor_pos:
                print(f"Last point: {self.points[-1]}, Cursor Position: {self.cursor_pos}")  # Debugging line

                cv2.line(frame, self.points[-1], self.cursor_pos, (0, 0, 255), 2)
