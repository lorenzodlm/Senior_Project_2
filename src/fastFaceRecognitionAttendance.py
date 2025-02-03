import os
import cv2
import face_recognition
import numpy as np
from scipy.spatial import distance as dist
import datetime
import pandas as pd
import pytz
import time
import threading
from queue import Queue
from collections import deque
import pickle

class FaceRecognitionAttendance:
    def __init__(self, dataset_path, pickle_file='face_encodings.pkl', mongo_collection=None):
        self.dataset_path = dataset_path
        self.pickle_file = pickle_file
        self.mongo_collection = mongo_collection
        self.known_face_encodings, self.known_user_ids = self.load_face_encodings()
        self.frame_queue = Queue(maxsize=10)
        self.result_queue = Queue()
        self.blink_history = {}
        self.EYE_AR_THRESH = 0.25
        self.EYE_AR_CONSEC_FRAMES = 3
        self.thailand_tz = pytz.timezone('Asia/Bangkok')
        self.blink_frame_buffer = 20  # Number of frames to consider for blink detection

    def load_face_encodings(self):
        # Try to load existing encodings from pickle file
        if os.path.exists(self.pickle_file):
            print("Loading existing face encodings from pickle file.")
            with open(self.pickle_file, 'rb') as f:
                known_face_encodings, known_user_ids = pickle.load(f)
        else:
            print("No pickle file found, creating new encodings.")
            known_face_encodings, known_user_ids = self.process_new_users()

        return known_face_encodings, known_user_ids

    def process_new_users(self):
        known_face_encodings = []
        known_user_ids = []
        
        for user_id in os.listdir(self.dataset_path):
            user_folder = os.path.join(self.dataset_path, user_id)
            if os.path.isdir(user_folder) and user_id not in known_user_ids:
                print(f"Processing images for user: {user_id}")
                for filename in os.listdir(user_folder):
                    if filename.endswith(".jpg") or filename.endswith(".png"):
                        img_path = os.path.join(user_folder, filename)
                        img = cv2.imread(img_path)
                        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        img_encodings = face_recognition.face_encodings(rgb_img)
                        if img_encodings:
                            img_encoding = img_encodings[0]
                            known_face_encodings.append(img_encoding)
                            known_user_ids.append(user_id)

        # Save the newly created encodings
        self.save_face_encodings(known_face_encodings, known_user_ids)
        return known_face_encodings, known_user_ids

    def save_face_encodings(self, known_face_encodings, known_user_ids):
        with open(self.pickle_file, 'wb') as f:
            pickle.dump((known_face_encodings, known_user_ids), f)
        print(f"Saved {len(known_face_encodings)} encodings to {self.pickle_file}")

    def fetch_data_from_mongo(self):
        try:
            mongo_data = list(self.mongo_collection.find({}, {'_id': 0}))
            if len(mongo_data) == 0:
                print("No data found in MongoDB.")
            else:
                print(f"Fetched {len(mongo_data)} records from MongoDB.")
            mongo_df = pd.DataFrame(mongo_data)
            return mongo_df
        except Exception as e:
            print(f"Error fetching data from MongoDB: {e}")
            return None

    def eye_aspect_ratio(self, eye):
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        C = dist.euclidean(eye[0], eye[3])
        ear = (A + B) / (2.0 * C)
        return ear

    def is_blinking(self, face_landmarks):
        left_eye = face_landmarks["left_eye"]
        right_eye = face_landmarks["right_eye"]
        left_ear = self.eye_aspect_ratio(left_eye)
        right_ear = self.eye_aspect_ratio(right_eye)
        avg_ear = (left_ear + right_ear) / 2.0
        return avg_ear < self.EYE_AR_THRESH

    def process_video_stream(self, matched_class_code):
        video_capture = cv2.VideoCapture(0)
        video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # Start worker threads
        for _ in range(3):  # Number of worker threads
            t = threading.Thread(target=self.worker, args=(matched_class_code,))
            t.daemon = True
            t.start()

        frame_count = 0
        start_time = time.time()
        processed_users = set()

        while True:
            ret, frame = video_capture.read()
            if not ret:
                print("Failed to capture video frame.")
                continue

            frame_count += 1
            small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            # Always process frames for blink detection
            self.frame_queue.put((rgb_small_frame, frame_count))

            if not self.result_queue.empty():
                user_id, is_real, confidence = self.result_queue.get()
                if user_id != "Unknown" and is_real and user_id not in processed_users:
                    self.log_attendance(user_id, matched_class_code)
                    processed_users.add(user_id)
                    print(f"Attendance logged for {user_id}")

                # Draw rectangle and text on the frame
                for (top, right, bottom, left), face_encoding in zip(face_recognition.face_locations(rgb_small_frame), face_recognition.face_encodings(rgb_small_frame)):
                    top *= 2
                    right *= 2
                    bottom *= 2
                    left *= 2
                    color = (0, 255, 0) if is_real else (0, 0, 255)
                    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                    label = f"{user_id} - {'Real' if is_real else 'Fake'} ({confidence:.2f}%)"
                    cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)

            # Display FPS
            end_time = time.time()
            fps = frame_count / (end_time - start_time)
            cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            cv2.imshow('Video', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        video_capture.release()
        cv2.destroyAllWindows()

    def worker(self, matched_class_code):
        frame_buffer = deque(maxlen=self.blink_frame_buffer)
        while True:
            rgb_small_frame, frame_count = self.frame_queue.get()
            if rgb_small_frame is None:
                break

            frame_buffer.append(rgb_small_frame)
            if len(frame_buffer) < self.blink_frame_buffer:
                continue

            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            for face_encoding, face_location in zip(face_encodings, face_locations):
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)

                if matches[best_match_index]:
                    user_id = self.known_user_ids[best_match_index]
                    confidence = (1 - face_distances[best_match_index]) * 100

                    # Process all frames in the buffer for blink detection
                    blink_detected = self.detect_blink_sequence(frame_buffer, face_location)

                    if blink_detected:
                        self.result_queue.put((user_id, True, confidence))
                    else:
                        self.result_queue.put((user_id, False, confidence))
                else:
                    self.result_queue.put(("Unknown", False, 0.0))

            self.frame_queue.task_done()

    def detect_blink_sequence(self, frame_buffer, face_location):
        ear_history = []
        for frame in frame_buffer:
            landmarks = face_recognition.face_landmarks(frame, [face_location])
            if landmarks:
                left_eye = landmarks[0]['left_eye']
                right_eye = landmarks[0]['right_eye']
                ear = (self.eye_aspect_ratio(left_eye) + self.eye_aspect_ratio(right_eye)) / 2.0
                ear_history.append(ear < self.EYE_AR_THRESH)

        # Check for a blink pattern in the sequence
        return sum(ear_history) >= self.EYE_AR_CONSEC_FRAMES and not all(ear_history)

    def log_attendance(self, user_id, matched_class_code):
        timestamp_utc = datetime.datetime.now(pytz.UTC)
        timestamp_thailand = timestamp_utc.astimezone(self.thailand_tz)

        try:
            if self.mongo_collection is not None:
                user_doc = self.mongo_collection.find_one({'UserID': user_id, 'classID': matched_class_code})

                if not user_doc:
                    result = self.mongo_collection.insert_one({
                        'UserID': user_id,
                        'attendance': [timestamp_thailand],
                        'classID': matched_class_code
                    })
                    print(f"Insertion result: {result.inserted_id}")
                else:
                    update_result = self.mongo_collection.update_one(
                        {'UserID': user_id, 'classID': matched_class_code},
                        {'$push': {'attendance': timestamp_thailand}}
                    )
                    print(f"Matched count: {update_result.matched_count}, Modified count: {update_result.modified_count}")

                print(f"Attendance logged for {user_id} in class {matched_class_code}")

        except Exception as e:
            print(f"Error logging attendance for {user_id}: {e}")
