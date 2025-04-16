from django.http import StreamingHttpResponse
from django.views.decorators import gzip
import cv2
import face_recognition
import mediapipe as mp
import numpy as np
from ultralytics import YOLO
import torch
from .models import KnownFace
from .models import AttendanceRecord
from django.core.files.base import ContentFile
from django.utils.timezone import now
from io import BytesIO
from PIL import Image


# Configuration
RTSP_URL = "rtsp://admin:admin123@192.168.100.70/cam/realmonitor?channel=7&subtype=1"

RESIZE_WIDTH = 640
RESIZE_HEIGHT = 360
SKIP_FRAMES = 2
POSE_AREA_COLOR = (0, 255, 255)
FACE_AREA_COLOR = (255, 255, 0)

def load_known_faces():
    face_encodings = {}
    for face in KnownFace.objects.all():
        try:
            image = face_recognition.load_image_file(face.image.path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                face_encodings[face.name] = {
                    "encoding": encodings[0],
                    "area": face.area_tuple()  # (x1, y1, x2, y2)
                }
        except Exception as e:
            print(f"Failed to process {face.name}: {e}")
    return face_encodings


def initialize_models():
    mp_face_detection = mp.solutions.face_detection
    face_detector = mp_face_detection.FaceDetection(min_detection_confidence=0.5)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    pose_model = YOLO("models/best.pt").to(device)

    return face_detector, pose_model


def draw_areas(frame, areas, color, label=None):
    for area in areas:
        x1, y1, x2, y2 = area
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        if label:
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)


def process_faces(frame, face_detector, face_encodings, recognized_faces=None):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_detector.process(rgb_frame)

    ih, iw = frame.shape[:2]

    if results.detections:
        for detection in results.detections:
            bboxC = detection.location_data.relative_bounding_box

            x1 = max(0, int(bboxC.xmin * iw))
            y1 = max(0, int(bboxC.ymin * ih))
            x2 = min(iw, x1 + int(bboxC.width * iw))
            y2 = min(ih, y1 + int(bboxC.height * ih))

            # Get center of the face box
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            # Skip detection if not inside any defined area
            inside_area = False
            for data in face_encodings.values():
                x_a, y_a, x_b, y_b = data["area"]
                if x_a <= center_x <= x_b and y_a <= center_y <= y_b:
                    inside_area = True
                    break

            if not inside_area:
                continue  # Skip this face

            # Proceed as usual
            face_location = [(y1, x2, y2, x1)]
            face_encodings_detected = face_recognition.face_encodings(rgb_frame, face_location)

            if face_encodings_detected:
                encoding = face_encodings_detected[0]
                known_encodings = [data["encoding"] for data in face_encodings.values()]
                match_results = face_recognition.compare_faces(known_encodings, encoding)
                face_distances = face_recognition.face_distance(known_encodings, encoding)

                if True in match_results:
                    match_index = match_results.index(True)
                    matched_name = list(face_encodings.keys())[match_index]
                    matched_area = face_encodings[matched_name]["area"]

                    if (matched_area[0] <= x1 <= matched_area[2] and
                        matched_area[1] <= y1 <= matched_area[3]):
                        print(f"✅ Check-in: {matched_name}")
                        label = f"{matched_name} (OK)"
                        color = (0, 255, 0)
                    else:
                        print(f"⚠️ Wrong area: {matched_name}")
                        label = f"{matched_name} (Wrong Area)"
                        color = (0, 0, 255)

                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                else:
                    print("❓ Unknown face detected.")
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(frame, "Unknown", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    return frame

def process_poses(frame, pose_model, pose_areas):
    results = pose_model(frame, verbose=False)[0]

    for box in results.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        in_area = any(area[0] <= center_x <= area[2] and
                      area[1] <= center_y <= area[3]
                      for area in pose_areas)

        if not in_area:
            continue  # Skip this pose box if not in area

        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        label = f"{results.names[cls_id]} {conf:.2f}"

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, label, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    return frame


import time  

def gen_frames():
    face_encodings = load_known_faces()
    face_detector, pose_model = initialize_models()
    pose_areas = [data["area"] for data in face_encodings.values()]
    recognized_faces = set()

    cap = cv2.VideoCapture(0)
    frame_interval = 1 / 2 
    last_processed_time = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        current_time = time.time()
        if (current_time - last_processed_time) < frame_interval:
            continue  
        last_processed_time = current_time
        frame = cv2.resize(frame, (RESIZE_WIDTH, RESIZE_HEIGHT))
        draw_areas(frame, [data["area"] for data in face_encodings.values()],
                   FACE_AREA_COLOR, "Area")

        frame = process_faces(frame, face_detector, face_encodings, recognized_faces)
        frame = process_poses(frame, pose_model, pose_areas)

        # Encode and stream the frame
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()

@gzip.gzip_page
def stream_view(request):
    return StreamingHttpResponse(gen_frames(),
                                 content_type='multipart/x-mixed-replace; boundary=frame')


ACTIVITY_MAPPING = {
    "sitting": "sleeping",
    "standing": "working",
}

def save_image_from_frame(frame):
    image_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    buffer = BytesIO()
    image_pil.save(buffer, format="JPEG")
    return ContentFile(buffer.getvalue(), name=f"{now().strftime('%Y%m%d_%H%M%S')}.jpg")

def handle_attendance(detected_person, frame, activity_type):
    record, created = AttendanceRecord.objects.get_or_create(
        name=detected_person,
        check_out_time__isnull=True,
        defaults={
            "check_in_time": now(),
            "person_image": save_image_from_frame(frame),
        }
    )

    record.activity_image = save_image_from_frame(frame)
    record.activity_type = activity_type
    record.working_time = now() if activity_type == "working" else record.working_time
    record.seleping_time = now() if activity_type == "sleeping" else record.seleping_time

    # Optional: Auto checkout after some logic
    # record.check_out_time = now()  

    record.save()