from flask import Flask, Response, render_template
import cv2
from hand_tracking_module import HandTracker
from creating_rectangles import RectangleDrawer
from flask import request
from flask import Flask, request, jsonify

class WebStream:
    def __init__(self, camera):
        self.app = Flask(__name__)
        self.camera = camera
        self.rectangle_drawer = RectangleDrawer()
        @self.app.route('/')
        def index():
            return render_template('index.html')

        @self.app.route('/video')
        def video():
            return Response(self.generate_frames(),
                            mimetype='multipart/x-mixed-replace; boundary=frame')


        @self.app.route('/key_event', methods=['POST'])
        def key_event():
            key = request.form['key']
                
            if key == '67':
                    # Handle 'c' key event. E.g., clear polygons.
                self.rectangle_drawer.clear_polygons()
            elif key == '27':
                    # Handle 'ESC' key event. E.g., cancel.
                self.rectangle_drawer.cancel()

            return '', 204
        @self.app.route('/coordinates', methods=['POST'])
        def coordinates():
            data = request.json
            x = data['x']
            y = data['y']
            self.rectangle_drawer.add_point(x, y)
            return jsonify(status="success"), 200
        @self.app.route('/mousemove', methods=['POST'])
        def mouse_move_event():
            data = request.json
            x = data['x']
            y = data['y']
            self.rectangle_drawer.mouse_move_event(x, y)
            return jsonify(status="success"), 200



    def generate_frames(self):
        hand_tracker = HandTracker()
        rectangle_drawer = self.rectangle_drawer
        
        # Set the resolution
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        while True:
            ret, frame = self.camera.read()
            
            if not ret:
                print("Failed to fetch frame")
                continue

            # Process the frame with hand tracking and rectangle drawing
            annotated_frame = hand_tracker.process_frame(frame, self.rectangle_drawer)
            self.rectangle_drawer.draw_polygon(annotated_frame)

            if rectangle_drawer.show_green_overlay:
                print("SHOWING GREEN OVERLAY")
                overlay = annotated_frame.copy()
                cv2.rectangle(overlay, (0, 0), (1280, 720), (0, 255, 0), -1)
                alpha = 0.3  # Transparency factor
                cv2.addWeighted(overlay, alpha, annotated_frame, 1 - alpha, 0, annotated_frame)

            elif rectangle_drawer.show_red_overlay and rectangle_drawer.show_green_overlay is False:
                translucent_layer = annotated_frame.copy()
                cv2.rectangle(translucent_layer, (0, 0), (1280, 720), (0, 0, 255), -1)
                cv2.addWeighted(translucent_layer, 0.3, annotated_frame, 0.7, 0, annotated_frame)

            # Convert the frame to JPEG
            _, buffer = cv2.imencode('.jpg', annotated_frame)

            # Send the frame as bytes
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')



    def run(self):
        self.app.run(host='0.0.0.0', port=5000)


# In your main code
camera = cv2.VideoCapture(0)
web_stream = WebStream(camera)
web_stream.run()
