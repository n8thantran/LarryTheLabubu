"""Hand Alternator Game - A CV-based game for the desktop pet system

Requirements:
- opencv-python (pip install opencv-python)  
- mediapipe (pip install mediapipe)
- numpy (pip install numpy)
- A working webcam/camera

The game will work in fallback mode (simulation only) if camera is not available.
"""

# Check for required dependencies
try:
    import cv2
    import numpy as np
    CV_BASIC_AVAILABLE = True
except ImportError as e:
    print(f"Basic CV dependencies not available: {e}")
    print("Install with: pip install opencv-python numpy")
    CV_BASIC_AVAILABLE = False
    cv2 = None
    np = None

# Check for mediapipe separately
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
    CV_AVAILABLE = CV_BASIC_AVAILABLE and True
except ImportError:
    print("Mediapipe not available - using camera-only mode")
    print("For full hand tracking install: pip install mediapipe")
    MEDIAPIPE_AVAILABLE = False
    CV_AVAILABLE = CV_BASIC_AVAILABLE  # Still works without mediapipe
    mp = None

import time
import random
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QPixmap, QImage, QFont
from .base_game import BaseGame


class CVWorkerThread(QThread):
    """Worker thread for CV processing to avoid blocking the UI"""
    frame_ready = Signal(object)  # Changed from np.ndarray to object for compatibility
    game_state_update = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.hand_alternator = None
        self.camera_id = 0
        self.camera_backend = cv2.CAP_ANY if CV_AVAILABLE else None
        
    def setup_cv(self):
        """Setup computer vision components"""
        if not CV_AVAILABLE:
            print("CV libraries not available - cannot setup camera")
            return False
            
        try:
            # Game state
            self.score = 0
            self.last_position = None  # "left_up" or "right_up"
            self.position_start_time = None
            self.hold_duration = 1.0  # seconds to hold position
            self.alternation_count = 0
            self.target_alternations = 10  # Win condition
            
            # Motion detection setup
            self.background_subtractor = cv2.createBackgroundSubtractorMOG2(detectShadows=False)
            self.previous_frame = None
            
            if MEDIAPIPE_AVAILABLE:
                # Initialize MediaPipe hand tracking
                print("✅ Using MediaPipe for accurate hand tracking")
                self.mp_hands = mp.solutions.hands
                self.hands = self.mp_hands.Hands(
                    static_image_mode=False,
                    max_num_hands=2,
                    min_detection_confidence=0.7,
                    min_tracking_confidence=0.5
                )
                self.mp_drawing = mp.solutions.drawing_utils
                self.use_hand_tracking = True
            else:
                # Use motion-based detection
                print("⚠️ Using motion detection (no MediaPipe)")
                self.use_hand_tracking = False
            
            # Camera - use the working camera ID and backend
            print(f"🎥 Setting up camera {self.camera_id} with backend {self.camera_backend}")
            self.cap = cv2.VideoCapture(self.camera_id, self.camera_backend)
            
            # Set properties for better performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer for lower latency
            
            is_opened = self.cap.isOpened()
            if is_opened:
                # Test read a frame
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    print(f"✅ CV worker camera initialized successfully!")
                    return True
                else:
                    print("❌ CV worker camera opened but can't read frames")
                    return False
            else:
                print("❌ CV worker camera failed to open")
                return False
            
        except Exception as e:
            print(f"CV setup failed: {e}")
            return False
    
    def get_hand_positions(self, landmarks, hand_label):
        """Extract key landmarks for position detection (MediaPipe method)"""
        wrist = landmarks.landmark[0]
        return {
            'wrist_y': wrist.y,
            'hand_label': hand_label
        }
    
    def detect_motion_regions(self, frame):
        """Detect motion in left and right regions (fallback method)"""
        height, width = frame.shape[:2]
        
        # Define left and right regions
        left_region = frame[:, :width//2]
        right_region = frame[:, width//2:]
        
        # Convert to grayscale for motion detection
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        if self.previous_frame is not None:
            # Calculate frame difference
            diff = cv2.absdiff(self.previous_frame, gray_frame)
            
            # Threshold the difference
            _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
            
            # Split into left and right regions
            left_thresh = thresh[:, :width//2]
            right_thresh = thresh[:, width//2:]
            
            # Count motion pixels in each region
            left_motion = cv2.countNonZero(left_thresh)
            right_motion = cv2.countNonZero(right_thresh)
            
            # Determine which side has more motion (indicating hand position)
            motion_threshold = 500  # Minimum pixels for detection
            
            left_active = left_motion > motion_threshold
            right_active = right_motion > motion_threshold
            
            # Store current frame for next comparison
            self.previous_frame = gray_frame.copy()
            
            return {
                'left_motion': left_motion,
                'right_motion': right_motion,
                'left_active': left_active,
                'right_active': right_active
            }
        else:
            # First frame, just store it
            self.previous_frame = gray_frame.copy()
            return None
    
    def determine_current_state(self, left_hand_pos, right_hand_pos):
        """Determine which hand is above the other (MediaPipe method)"""
        if left_hand_pos is None or right_hand_pos is None:
            return None
        
        # Lower y value means higher position on screen
        if left_hand_pos['wrist_y'] < right_hand_pos['wrist_y'] - 0.05:
            return "left_up"
        elif right_hand_pos['wrist_y'] < left_hand_pos['wrist_y'] - 0.05:
            return "right_up"
        else:
            return "neutral"
    
    def determine_current_state_motion(self, motion_data):
        """Determine current state using motion detection (fallback method)"""
        if motion_data is None:
            return None
            
        left_active = motion_data['left_active']
        right_active = motion_data['right_active']
        
        if left_active and not right_active:
            return "left_up"
        elif right_active and not left_active:
            return "right_up"
        elif left_active and right_active:
            # Both sides active - determine which has more motion
            if motion_data['left_motion'] > motion_data['right_motion'] * 1.2:
                return "left_up"
            elif motion_data['right_motion'] > motion_data['left_motion'] * 1.2:
                return "right_up"
            else:
                return "neutral"
        else:
            return "neutral"
    
    def update_game_state(self, current_state):
        """Update game logic based on current hand positions"""
        current_time = time.time()
        
        if current_state is None or current_state == "neutral":
            self.position_start_time = None
            return "Show both hands clearly"
        
        # Check if this is a new position
        if current_state != self.last_position:
            self.position_start_time = current_time
            
            # Check for successful alternation
            if self.last_position is not None and self.last_position != "neutral":
                if ((self.last_position == "left_up" and current_state == "right_up") or
                    (self.last_position == "right_up" and current_state == "left_up")):
                    self.alternation_count += 1
                    self.score += 10
            
            self.last_position = current_state
            return f"Hold {current_state.replace('_', ' ')} position..."
        
        # Check if position has been held long enough
        if self.position_start_time and current_time - self.position_start_time >= self.hold_duration:
            return f"Good! Now switch to the opposite position"
        
        # Calculate remaining time
        if self.position_start_time:
            remaining_time = self.hold_duration - (current_time - self.position_start_time)
            return f"Hold for {remaining_time:.1f}s more..."
        
        return "Hold position..."
    
    def process_frame(self, frame):
        """Process a single frame"""
        frame = cv2.flip(frame, 1)
        height, width = frame.shape[:2]
        
        if self.use_hand_tracking and MEDIAPIPE_AVAILABLE:
            # Use MediaPipe hand tracking
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)
            
            left_hand_pos = None
            right_hand_pos = None
            
            if results.multi_hand_landmarks and results.multi_handedness:
                for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                    # Draw hand landmarks
                    self.mp_drawing.draw_landmarks(
                        frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    
                    # Get hand label
                    hand_label = handedness.classification[0].label
                    hand_pos = self.get_hand_positions(hand_landmarks, hand_label)
                    
                    if hand_label == "Left":
                        left_hand_pos = hand_pos
                    else:
                        right_hand_pos = hand_pos
            
            # Determine current state and update game
            current_state = self.determine_current_state(left_hand_pos, right_hand_pos)
            
        else:
            # Use motion detection fallback
            motion_data = self.detect_motion_regions(frame)
            current_state = self.determine_current_state_motion(motion_data)
            
            # Draw detection zones
            cv2.line(frame, (width//2, 0), (width//2, height), (255, 255, 255), 2)
            cv2.putText(frame, "LEFT", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(frame, "RIGHT", (width//2 + 50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Show motion indicators
            if motion_data:
                left_color = (0, 255, 0) if motion_data['left_active'] else (0, 0, 255)
                right_color = (0, 255, 0) if motion_data['right_active'] else (0, 0, 255)
                cv2.circle(frame, (100, 100), 20, left_color, -1)
                cv2.circle(frame, (width//2 + 100, 100), 20, right_color, -1)
        
        # Update game state
        status_text = self.update_game_state(current_state)
        
        # Draw current state on frame
        state_text = f"State: {current_state}" if current_state else "State: None"
        cv2.putText(frame, state_text, (10, height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        # Emit game state
        game_state = {
            'score': self.score,
            'alternations': self.alternation_count,
            'target': self.target_alternations,
            'status': status_text,
            'won': self.alternation_count >= self.target_alternations,
            'lost': False  # Time-based loss will be handled by main game
        }
        self.game_state_update.emit(game_state)
        
        return frame
    
    def run(self):
        """Main CV processing loop"""
        if not self.setup_cv():
            return
            
        self.running = True
        
        while self.running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break
                
            processed_frame = self.process_frame(frame)
            self.frame_ready.emit(processed_frame)
            
            # Small delay to prevent overwhelming the UI
            self.msleep(33)  # ~30 FPS
        
        # Cleanup
        if hasattr(self, 'cap'):
            self.cap.release()
    
    def stop(self):
        """Stop the CV processing"""
        self.running = False
        self.wait()


class HandAlternatorGame(BaseGame):
    def __init__(self):
        super().__init__()
        
        # Game metadata
        self.game_name = "Hand Alternator"
        self.game_description = "Use your hands to alternate positions!"
        self.play_duration = 30  # 30 seconds to complete
        
        self.setWindowTitle(self.game_name)
        self.setFixedSize(800, 600)
        self.setStyleSheet("background-color: #1a1a2e;")
        
        # Game state
        self.game_time = 30.0
        self.start_time = None
        self.target_alternations = 10
        self.current_score = 0
        self.current_alternations = 0
        
        # Camera availability (check first)
        self.camera_available = False
        self.working_camera_id = 0
        self.working_backend = cv2.CAP_ANY if CV_AVAILABLE else None
        self.check_camera()
        
        # CV worker thread (setup after camera check)
        self.cv_worker = CVWorkerThread()
        self.cv_worker.camera_id = self.working_camera_id
        self.cv_worker.camera_backend = self.working_backend
        self.cv_worker.frame_ready.connect(self.update_camera_display)
        self.cv_worker.game_state_update.connect(self.update_game_display)
        
        # Setup UI
        self.setup_ui()
        
        # Game timer
        self.game_timer = QTimer()
        self.game_timer.timeout.connect(self.update_time)
        
    def check_camera(self):
        """Check if camera is available with comprehensive testing"""
        print("🔍 Checking camera availability...")
        
        if not CV_AVAILABLE:
            print("❌ CV libraries not available")
            self.camera_available = False
            return
            
        # Try multiple camera indices and backends
        camera_indices = [0, 1, 2]  # Try different camera IDs
        backends = [cv2.CAP_ANY, cv2.CAP_DSHOW, cv2.CAP_V4L2] if CV_AVAILABLE else [None]
        
        for camera_id in camera_indices:
            for backend in backends:
                if backend is None:
                    continue
                    
                try:
                    print(f"🎥 Testing camera {camera_id} with backend {backend}")
                    cap = cv2.VideoCapture(camera_id, backend)
                    
                    # Set properties for better compatibility
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480) 
                    cap.set(cv2.CAP_PROP_FPS, 30)
                    
                    if cap.isOpened():
                        # Try to read a frame to make sure camera actually works
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            print(f"✅ Camera {camera_id} working! Frame size: {frame.shape}")
                            cap.release()
                            self.camera_available = True
                            self.working_camera_id = camera_id
                            self.working_backend = backend
                            return
                        else:
                            print(f"❌ Camera {camera_id} opened but can't read frames")
                    else:
                        print(f"❌ Camera {camera_id} with backend {backend} failed to open")
                    
                    cap.release()
                    
                except Exception as e:
                    print(f"❌ Camera {camera_id} error: {e}")
                    try:
                        cap.release()
                    except:
                        pass
        
        print("❌ No working camera found")
        self.camera_available = False
        self.working_camera_id = 0
        self.working_backend = cv2.CAP_ANY if CV_AVAILABLE else None
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        
        self.time_label = QLabel("Time: 30s")
        self.time_label.setStyleSheet("color: #ff6b6b; font-size: 24px; font-weight: bold;")
        
        self.score_label = QLabel("Score: 0")
        self.score_label.setStyleSheet("color: #4ecdc4; font-size: 20px; font-weight: bold;")
        
        header_layout.addWidget(self.time_label)
        header_layout.addStretch()
        header_layout.addWidget(self.score_label)
        
        layout.addLayout(header_layout)
        
        # Progress
        self.progress_label = QLabel(f"Alternations: 0 / {self.target_alternations}")
        self.progress_label.setStyleSheet("color: #ffe66d; font-size: 18px; font-weight: bold;")
        layout.addWidget(self.progress_label)
        
        # Camera display or message
        if self.camera_available:
            self.camera_label = QLabel()
            self.camera_label.setFixedSize(640, 480)
            self.camera_label.setStyleSheet("border: 2px solid #4ecdc4; background-color: #16213e;")
            self.camera_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.camera_label)
            
            # Status
            self.status_label = QLabel("Get ready to alternate your hands!")
            self.status_label.setStyleSheet("color: #a8e6cf; font-size: 16px;")
            layout.addWidget(self.status_label)
        else:
            # No camera fallback
            self.fallback_label = QLabel("📷 CAMERA NOT AVAILABLE 📷\n\nThis game requires a webcam.\nPlease connect a camera and restart the game.")
            self.fallback_label.setStyleSheet("color: #ff6b6b; font-size: 18px; text-align: center;")
            self.fallback_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.fallback_label)
            
            # Fallback controls for testing
            button_layout = QHBoxLayout()
            
            self.simulate_button = QPushButton("Simulate Success")
            self.simulate_button.clicked.connect(self.simulate_alternation)
            self.simulate_button.setStyleSheet("background-color: #4ecdc4; color: white; font-size: 14px; padding: 10px;")
            
            self.retry_camera_button = QPushButton("🔄 Retry Camera")
            self.retry_camera_button.clicked.connect(self.retry_camera_setup)
            self.retry_camera_button.setStyleSheet("background-color: #ffe66d; color: black; font-size: 14px; padding: 10px;")
            
            button_layout.addWidget(self.simulate_button)
            button_layout.addWidget(self.retry_camera_button)
            layout.addLayout(button_layout)
        
        # Instructions
        instructions = QLabel(
            "INSTRUCTIONS:\n"
            "1. Show both hands to the camera\n"
            "2. Alternate which hand is higher\n" 
            "3. Hold each position for 1 second\n"
            f"4. Complete {self.target_alternations} alternations to win!"
        )
        instructions.setStyleSheet("color: #ddd; font-size: 12px; padding: 10px;")
        layout.addWidget(instructions)
        
        self.setLayout(layout)
    
    def simulate_alternation(self):
        """Simulate an alternation for testing without camera"""
        if self.game_active:
            self.current_alternations += 1
            self.current_score += 10
            self.update_labels()
            
            if self.current_alternations >= self.target_alternations:
                self.game_won = True
                self.game_active = False
                self.trigger_game_end_callback()
    
    def retry_camera_setup(self):
        """Retry camera setup after user fixes issues"""
        print("🔄 Retrying camera setup...")
        old_camera_available = self.camera_available
        
        # Re-check camera availability
        self.check_camera()
        
        if self.camera_available and not old_camera_available:
            print("✅ Camera now available! Restarting game with camera...")
            
            # Update UI to camera mode
            self.fallback_label.setParent(None)
            self.simulate_button.setParent(None)
            self.retry_camera_button.setParent(None)
            
            # Recreate UI with camera
            self.setup_camera_ui()
            
            # Update CV worker with new camera settings
            self.cv_worker.camera_id = self.working_camera_id
            self.cv_worker.camera_backend = self.working_backend
            
            self.show_comment("📷 Camera activated! Get ready to play with hand tracking!")
        else:
            print("❌ Camera still not available")
            self.show_comment("❌ Camera still not working. Check connection and permissions.")
    
    def setup_camera_ui(self):
        """Setup the camera UI elements"""
        # Find the layout and add camera elements
        layout = self.layout()
        
        # Camera display
        self.camera_label = QLabel()
        self.camera_label.setFixedSize(640, 480)
        self.camera_label.setStyleSheet("border: 2px solid #4ecdc4; background-color: #16213e;")
        self.camera_label.setAlignment(Qt.AlignCenter)
        layout.insertWidget(3, self.camera_label)  # Insert after progress label
        
        # Status
        self.status_label = QLabel("Get ready to alternate your hands!")
        self.status_label.setStyleSheet("color: #a8e6cf; font-size: 16px;")
        layout.insertWidget(4, self.status_label)
    
    def show_comment(self, message):
        """Show a comment (interface with main pet system)"""
        print(f"Hand Game: {message}")  # For now, just print
    
    def update_camera_display(self, frame):
        """Update the camera display with new frame"""
        if not self.game_active:
            return
            
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        
        # Scale image to fit label
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(self.camera_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.camera_label.setPixmap(scaled_pixmap)
    
    def update_game_display(self, game_state):
        """Update game display with new state"""
        if not self.game_active:
            return
            
        self.current_score = game_state['score']
        self.current_alternations = game_state['alternations']
        
        self.update_labels()
        
        if hasattr(self, 'status_label'):
            self.status_label.setText(game_state['status'])
        
        # Check win condition
        if game_state['won'] and not self.game_won:
            self.game_won = True
            self.game_active = False
            self.trigger_game_end_callback()
    
    def update_labels(self):
        """Update score and progress labels"""
        self.score_label.setText(f"Score: {self.current_score}")
        self.progress_label.setText(f"Alternations: {self.current_alternations} / {self.target_alternations}")
        
        # Change color based on progress
        if self.current_alternations >= self.target_alternations:
            self.progress_label.setStyleSheet("color: #4ecdc4; font-size: 18px; font-weight: bold;")
        elif self.current_alternations >= self.target_alternations * 0.7:
            self.progress_label.setStyleSheet("color: #ffe66d; font-size: 18px; font-weight: bold;")
        else:
            self.progress_label.setStyleSheet("color: #ff6b6b; font-size: 18px; font-weight: bold;")
    
    def update_time(self):
        """Update game timer"""
        if not self.game_active:
            return
            
        if self.start_time:
            elapsed = time.time() - self.start_time
            self.game_time = max(0, 30.0 - elapsed)
            
        self.time_label.setText(f"Time: {int(self.game_time)}s")
        
        # Time-based lose condition
        if self.game_time <= 0 and not self.game_won and not self.game_lost:
            self.game_lost = True
            self.game_active = False
            if hasattr(self, 'status_label'):
                self.status_label.setText("⏰ Time's up! Try again!")
            else:
                self.fallback_label.setText("⏰ TIME'S UP! ⏰\n\nYou didn't complete enough alternations in time.\nBetter luck next time!")
            self.trigger_game_end_callback()
    
    def start_game(self):
        """Start the hand alternator game"""
        self.reset_game()
        self.game_active = True
        self.start_time = time.time()
        
        if self.camera_available:
            self.cv_worker.start()
        else:
            # Fallback mode - just run timer
            if hasattr(self, 'fallback_label'):
                self.fallback_label.setText("📷 NO CAMERA MODE 📷\n\nClick 'Simulate Success' to test\nor connect a camera for the real game!")
        
        self.game_timer.start(100)  # Update every 100ms
        print(f"Started {self.game_name}")
    
    def end_game(self):
        """End the game"""
        print(f"🎮 Ending {self.game_name}...")
        self.game_active = False
        
        # Stop game timer
        if hasattr(self, 'game_timer'):
            self.game_timer.stop()
        
        # Stop CV worker safely
        if hasattr(self, 'cv_worker') and self.cv_worker:
            print("🔄 Stopping CV worker...")
            self.cv_worker.stop()
            print("✅ CV worker stopped")
        
        print(f"✅ {self.game_name} ended successfully")
    
    def is_game_finished(self):
        """Check if game is finished"""
        return self.game_won or self.game_lost
    
    def reset_game(self):
        """Reset game state"""
        super().reset_game()
        self.game_time = 30.0
        self.current_score = 0
        self.current_alternations = 0
        self.update_labels()
        
        if hasattr(self, 'status_label'):
            self.status_label.setText("Get ready to alternate your hands!")
    
    def closeEvent(self, event):
        """Handle window close event - only close this game window"""
        print(f"🎮 Hand Alternator game window closing...")
        
        # Stop CV worker if running
        if hasattr(self, 'cv_worker') and self.cv_worker:
            self.cv_worker.stop()
        
        # End game properly
        if self.game_active:
            self.end_game()
        
        # Accept the close event (only closes this window)
        event.accept()
        print("✅ Hand Alternator game window closed - pet continues running!")
