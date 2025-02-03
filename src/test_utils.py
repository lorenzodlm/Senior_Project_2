import cv2
import numpy as np
import time
from threading import Thread
import os

class TestUtilities:
    @staticmethod
    def generate_test_frame(width=640, height=480, with_face=True):
        """Generate a test frame for face recognition testing"""
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        if with_face:
            # Add a simple face-like shape
            center_x, center_y = width // 2, height // 2
            # Draw face outline
            cv2.circle(frame, (center_x, center_y), 50, (255, 255, 255), -1)
            # Draw eyes
            cv2.circle(frame, (center_x - 20, center_y - 10), 10, (0, 0, 0), -1)
            cv2.circle(frame, (center_x + 20, center_y - 10), 10, (0, 0, 0), -1)
            # Draw mouth
            cv2.ellipse(frame, (center_x, center_y + 10), (20, 10), 0, 0, 180, (0, 0, 0), -1)
        return frame

    @staticmethod
    def simulate_blink(frame, duration=0.2):
        """Simulate a blink by modifying eye regions"""
        height, width = frame.shape[:2]
        center_x, center_y = width // 2, height // 2
        
        # Create a copy of the frame
        blinking_frame = frame.copy()
        
        # Draw closed eyes
        cv2.line(blinking_frame, (center_x - 25, center_y - 10), 
                 (center_x - 15, center_y - 10), (0, 0, 0), 2)
        cv2.line(blinking_frame, (center_x + 15, center_y - 10), 
                 (center_x + 25, center_y - 10), (0, 0, 0), 2)
        
        return blinking_frame

    @staticmethod
    def simulate_motion(frame, displacement=10):
        """Simulate motion by shifting the frame"""
        height, width = frame.shape[:2]
        M = np.float32([[1, 0, displacement], [0, 1, displacement]])
        return cv2.warpAffine(frame, M, (width, height))

    class MockGPIO:
        """Mock class for testing GPIO functionality"""
        OUT = 'out'
        IN = 'in'
        HIGH = 1
        LOW = 0
        FALLING = 'falling'
        PUD_UP = 'up'
        BCM = 'bcm'

        @staticmethod
        def setmode(mode):
            pass

        @staticmethod
        def setup(pin, mode, pull_up_down=None):
            pass

        @staticmethod
        def output(pin, value):
            pass

        @staticmethod
        def input(pin):
            return 0

        @staticmethod
        def cleanup():
            pass

        @staticmethod
        def add_event_detect(pin, edge, callback=None, bouncetime=None):
            pass

    @staticmethod
    def create_test_dataset(base_path, num_users=5, images_per_user=10):
        """Create a test dataset for face recognition"""
        for user_id in range(num_users):
            user_dir = os.path.join(base_path, f"user_{user_id}")
            os.makedirs(user_dir, exist_ok=True)
            
            for img_id in range(images_per_user):
                frame = TestUtilities.generate_test_frame(with_face=True)
                cv2.imwrite(os.path.join(user_dir, f"face_{img_id}.jpg"), frame)

    @staticmethod
    def simulate_camera_feed(callback, duration=10, fps=30):
        """Simulate a camera feed for testing"""
        start_time = time.time()
        frame_time = 1.0 / fps
        
        while (time.time() - start_time) < duration:
            frame = TestUtilities.generate_test_frame()
            callback(frame)
            time.sleep(frame_time)

class PerformanceMonitor:
    def __init__(self):
        self.start_time = None
        self.frame_count = 0
        self.fps_history = []

    def start(self):
        """Start monitoring performance"""
        self.start_time = time.time()
        self.frame_count = 0
        self.fps_history.clear()

    def update(self):
        """Update frame count"""
        self.frame_count += 1
        elapsed_time = time.time() - self.start_time
        if elapsed_time >= 1.0:  # Calculate FPS every second
            fps = self.frame_count / elapsed_time
            self.fps_history.append(fps)
            self.start_time = time.time()
            self.frame_count = 0

    def get_average_fps(self):
        """Get average FPS"""
        return np.mean(self.fps_history) if self.fps_history else 0

    def get_performance_metrics(self):
        """Get detailed performance metrics"""
        return {
            'average_fps': self.get_average_fps(),
            'min_fps': min(self.fps_history) if self.fps_history else 0,
            'max_fps': max(self.fps_history) if self.fps_history else 0,
            'fps_stability': np.std(self.fps_history) if self.fps_history else 0
        }

class SystemTester:
    def __init__(self, face_recognition_system):
        self.system = face_recognition_system
        self.performance_monitor = PerformanceMonitor()

    def run_full_test(self):
        """Run a comprehensive system test"""
        results = {
            'face_detection': self.test_face_detection(),
            'blink_detection': self.test_blink_detection(),
            'motion_detection': self.test_motion_detection(),
            'performance': self.test_performance(),
            'door_control': self.test_door_control()
        }
        return results

    def test_face_detection(self):
        """Test face detection capabilities"""
        test_frame = TestUtilities.generate_test_frame(with_face=True)
        try:
            result = self.system.process_single_frame(test_frame)
            return {'success': True, 'faces_detected': len(result) if result else 0}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def test_blink_detection(self):
        """Test blink detection"""
        normal_frame = TestUtilities.generate_test_frame()
        blink_frame = TestUtilities.simulate_blink(normal_frame)
        
        results = []
        for frame in [normal_frame, blink_frame]:
            try:
                result = self.system.detect_blink(frame)
                results.append(result)
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        return {'success': True, 'blink_detected': any(results)}

    def test_motion_detection(self):
        """Test motion detection"""
        frame1 = TestUtilities.generate_test_frame()
        frame2 = TestUtilities.simulate_motion(frame1)
        
        try:
            result1 = self.system.detect_motion(frame1)
            result2 = self.system.detect_motion(frame2)
            return {'success': True, 'motion_detected': result2}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def test_performance(self):
        """Test system performance"""
        self.performance_monitor.start()
        
        def process_frame(frame):
            self.system.process_single_frame(frame)
            self.performance_monitor.update()

        TestUtilities.simulate_camera_feed(process_frame, duration=5)
        return self.performance_monitor.get_performance_metrics()

    def test_door_control(self):
        """Test door control functionality"""
        try:
            # Test normal operation
            unlock_result = self.system.door_controller.unlock_door()
            time.sleep(1)
            lock_result = self.system.door_controller.lock_door()
            
            # Test emergency override
            emergency_result = self.system.door_controller.emergency_override_callback(None)
            
            return {
                'success': True,
                'unlock_operation': unlock_result,
                'lock_operation': lock_result,
                'emergency_override': emergency_result
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}


# This test utilities file provides:
# 1. Test frame generation for face recognition
# 2. Mock GPIO functionality for testing without hardware
# 3. Performance monitoring tools
# 4. Comprehensive system testing capabilities

# To use these utilities:

# 1. Import in your test files:
# ```python
# from src.test_utils import TestUtilities, PerformanceMonitor, SystemTester
# ```

# 2. Use in your tests:
# ```python
# def test_system():
#     tester = SystemTester(your_face_recognition_system)
#     results = tester.run_full_test()
#     print(results)
# ```

# Would you like me to provide more testing utilities or explain how to use these in specific test scenarios?