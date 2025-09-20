import cv2
import mediapipe as mp
import numpy as np
import time

class HandAlternator:
    def __init__(self):
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Game state
        self.score = 0
        self.last_position = None  # "left_up" or "right_up"
        self.position_start_time = None
        self.hold_duration = 1.0  # seconds to hold position
        self.alternation_count = 0
        
        # UI colors
        self.GREEN = (0, 255, 0)
        self.RED = (0, 0, 255)
        self.BLUE = (255, 0, 0)
        self.WHITE = (255, 255, 255)
        self.YELLOW = (0, 255, 255)
        
    def get_hand_positions(self, landmarks, hand_label):
        """Extract key landmarks for position detection"""
        # Get wrist position (landmark 0)
        wrist = landmarks.landmark[0]
        return {
            'wrist_y': wrist.y,
            'hand_label': hand_label
        }
    
    def determine_current_state(self, left_hand_pos, right_hand_pos):
        """Determine which hand is above the other"""
        if left_hand_pos is None or right_hand_pos is None:
            return None
        
        # Lower y value means higher position on screen
        if left_hand_pos['wrist_y'] < right_hand_pos['wrist_y'] - 0.05:  # Add threshold
            return "left_up"
        elif right_hand_pos['wrist_y'] < left_hand_pos['wrist_y'] - 0.05:
            return "right_up"
        else:
            return "neutral"  # Hands are at similar height
    
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
    
    def draw_ui(self, image, status_text, left_hand_pos, right_hand_pos, current_state):
        """Draw UI elements on the image"""
        height, width = image.shape[:2]
        
        # Draw header background
        cv2.rectangle(image, (0, 0), (width, 120), (0, 0, 0), -1)
        
        # Draw title
        cv2.putText(image, "Hand Alternator", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, self.WHITE, 2)
        
        # Draw score and stats
        cv2.putText(image, f"Score: {self.score}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.YELLOW, 2)
        cv2.putText(image, f"Alternations: {self.alternation_count}", (10, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.YELLOW, 2)
        
        # Draw instructions
        instructions = [
            "Instructions:",
            "1. Show both hands to camera",
            "2. Alternate which hand is higher",
            "3. Hold each position for 1 second",
            "Press 'q' to quit"
        ]
        
        for i, instruction in enumerate(instructions):
            color = self.WHITE if i == 0 else (200, 200, 200)
            cv2.putText(image, instruction, (width - 350, 25 + i * 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Draw status
        status_color = self.GREEN if "Good!" in status_text else self.WHITE
        cv2.putText(image, status_text, (10, height - 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
        
        # Draw hand position indicators
        if left_hand_pos and right_hand_pos:
            left_y = int(left_hand_pos['wrist_y'] * height)
            right_y = int(right_hand_pos['wrist_y'] * height)
            
            # Draw position lines
            cv2.line(image, (50, left_y), (150, left_y), self.BLUE, 3)
            cv2.putText(image, "L", (20, left_y + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.BLUE, 2)
            
            cv2.line(image, (width - 150, right_y), (width - 50, right_y), self.RED, 3)
            cv2.putText(image, "R", (width - 40, right_y + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.RED, 2)
            
            # Highlight current state
            if current_state == "left_up":
                cv2.circle(image, (100, left_y), 15, self.GREEN, 3)
            elif current_state == "right_up":
                cv2.circle(image, (width - 100, right_y), 15, self.GREEN, 3)

    def run(self):
        """Main application loop"""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("Error: Could not open camera")
            return
        
        print("Hand Alternator started!")
        print("Show both hands and alternate which one is higher")
        print("Press 'q' to quit")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process hands
            results = self.hands.process(rgb_frame)
            
            left_hand_pos = None
            right_hand_pos = None
            
            if results.multi_hand_landmarks and results.multi_handedness:
                for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                    # Draw hand landmarks
                    self.mp_drawing.draw_landmarks(
                        frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    
                    # Get hand label (Left or Right from camera perspective)
                    hand_label = handedness.classification[0].label
                    hand_pos = self.get_hand_positions(hand_landmarks, hand_label)
                    
                    if hand_label == "Left":  # Left hand from camera perspective
                        left_hand_pos = hand_pos
                    else:  # Right hand from camera perspective
                        right_hand_pos = hand_pos
            
            # Determine current state and update game
            current_state = self.determine_current_state(left_hand_pos, right_hand_pos)
            status_text = self.update_game_state(current_state)
            
            # Draw UI
            self.draw_ui(frame, status_text, left_hand_pos, right_hand_pos, current_state)
            
            # Display frame
            cv2.imshow('Hand Alternator', frame)
            
            # Check for quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        print(f"\nGame Over! Final Score: {self.score}")
        print(f"Total Alternations: {self.alternation_count}")

if __name__ == "__main__":
    app = HandAlternator()
    app.run()
