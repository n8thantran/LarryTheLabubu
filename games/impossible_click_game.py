#!/usr/bin/env python3
"""
Impossible Labubu Clicking Game - A deliberately impossible game where you try to click Labubu but it keeps moving away!
"""

import random
import time
import math
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QFont, QPainter, QBrush, QColor, QPen
from games.base_game import BaseGame


class ImpossibleClickGame(BaseGame):
    def __init__(self):
        super().__init__()
        self.game_name = "Click the Labubu!"
        self.game_description = "Try to click the moving Labubu... if you can!"
        self.play_duration = 15  # 15 seconds of impossible clicking

        # Game state
        self.start_time = None
        self.clicks_attempted = 0
        self.successful_clicks = 0  # This will always be 0 because it's impossible
        self.labubu_position = QPoint(200, 200)
        self.labubu_size = 50
        self.is_hovering = False

        # Movement system
        self.movement_timer = QTimer()
        self.movement_timer.timeout.connect(self.move_labubu_away)
        self.movement_timer.setInterval(50)  # Move every 50ms for smooth evasion

        # Taunt timer
        self.taunt_timer = QTimer()
        self.taunt_timer.timeout.connect(self.show_taunt)
        self.taunt_timer.setInterval(2000)  # Taunt every 2 seconds

        self.taunts = [
            "Too slow! labu-labu!",
            "Can't catch me!",
            "I'm too fast for you!",
            "Nice try, SLOWPOKE!",
            "You'll NEVER click me!",
            "This is impossible and you know it!",
            "labuubuulabuubuu! *runs away*",
            "Your mouse skills are TERRIBLE!",
            "I'm untouchable!",
            "Give up already!",
            "forty-one ways to avoid your clicks!",
            "six seven times faster than you!"
        ]

        self.setup_ui()

    def setup_ui(self):
        """Set up the game UI"""
        self.setWindowTitle(self.game_name)
        self.setGeometry(100, 100, 700, 600)  # Made bigger
        self.setStyleSheet("""
            background-color: #FFE5F1;
            border: 3px solid #FF69B4;
        """)

        # Create a container widget for the top UI elements only
        top_widget = QWidget()
        top_widget.setFixedHeight(120)  # Fixed height so it doesn't interfere with game area
        top_layout = QVBoxLayout(top_widget)

        # Instructions
        self.instructions = QLabel("Click the pink Labubu to win! (Spoiler: It's impossible!)")
        self.instructions.setFont(QFont("Arial", 12, QFont.Bold))
        self.instructions.setAlignment(Qt.AlignCenter)
        self.instructions.setStyleSheet("color: #FF1493; margin: 5px;")
        top_layout.addWidget(self.instructions)

        # Score display
        self.score_label = QLabel("Clicks attempted: 0 | Successful: 0 | Time left: 15s")
        self.score_label.setFont(QFont("Arial", 10))
        self.score_label.setAlignment(Qt.AlignCenter)
        self.score_label.setStyleSheet("color: #8B008B; margin: 5px;")
        top_layout.addWidget(self.score_label)

        # Taunt display
        self.taunt_label = QLabel("Try to click me! labu-labu!")
        self.taunt_label.setFont(QFont("Arial", 10))
        self.taunt_label.setAlignment(Qt.AlignCenter)
        self.taunt_label.setStyleSheet("color: #FF4500; margin: 5px; font-style: italic;")
        top_layout.addWidget(self.taunt_label)

        # Main layout - put UI at top, leave rest of space for game area
        main_layout = QVBoxLayout()
        main_layout.addWidget(top_widget)
        main_layout.addStretch()  # This pushes the UI to the top and leaves space below

        self.setLayout(main_layout)

        # Enable mouse tracking for hover detection
        self.setMouseTracking(True)

    def start_game(self):
        """Start the impossible clicking game"""
        self.game_active = True
        self.start_time = time.time()
        self.clicks_attempted = 0
        self.successful_clicks = 0

        # Reset Labubu position - start in the clear game area below the UI
        self.labubu_position = QPoint(350, 350)  # Lower in the window, clear of UI

        # Start timers
        self.movement_timer.start()
        self.taunt_timer.start()

        # Game duration timer
        self.game_timer = QTimer()
        self.game_timer.timeout.connect(self.check_game_time)
        self.game_timer.start(100)  # Check every 100ms

        self.show()
        self.activateWindow()
        self.raise_()

        print("Impossible Labubu clicking game started!")

    def end_game(self):
        """End the game"""
        self.game_active = False

        # Stop all timers
        self.movement_timer.stop()
        self.taunt_timer.stop()
        if hasattr(self, 'game_timer'):
            self.game_timer.stop()

        # This game is always lost because it's impossible
        self.game_lost = True
        self.game_won = False

        # Show final taunt
        self.taunt_label.setText("GAME OVER! I told you it was impossible! labu-labu!")

        print(f"Impossible game ended! Clicks attempted: {self.clicks_attempted}, Successful: {self.successful_clicks}")

        # Callback to pet system
        if self.game_result_callback:
            try:
                self.game_result_callback(False, True, self.game_name)
            except Exception as e:
                print(f"Error in game result callback: {e}")

        # Hide the window after 2 seconds instead of closing it
        QTimer.singleShot(2000, self.hide)

    def is_game_finished(self):
        """Check if game is finished"""
        if not self.start_time:
            return False
        return time.time() - self.start_time >= self.play_duration

    def check_game_time(self):
        """Check game time and update display"""
        if not self.game_active or not self.start_time:
            return

        elapsed = time.time() - self.start_time
        time_left = max(0, self.play_duration - elapsed)

        self.score_label.setText(f"Clicks attempted: {self.clicks_attempted} | Successful: {self.successful_clicks} | Time left: {time_left:.1f}s")

        if self.is_game_finished():
            self.end_game()

    def move_labubu_away(self):
        """Move Labubu away from the mouse cursor"""
        if not self.game_active:
            return

        # Get mouse position relative to this widget
        mouse_pos = self.mapFromGlobal(self.cursor().pos())

        # Calculate distance from mouse to Labubu
        dx = self.labubu_position.x() - mouse_pos.x()
        dy = self.labubu_position.y() - mouse_pos.y()
        distance = math.sqrt(dx*dx + dy*dy)

        # If mouse is too close, move away!
        if distance < 100:  # Start moving when mouse gets within 100 pixels
            # Move away from mouse
            if distance > 0:
                # Normalize the direction vector
                move_x = (dx / distance) * 15  # Move 15 pixels away
                move_y = (dy / distance) * 15
            else:
                # If exactly on top, move randomly
                move_x = random.uniform(-20, 20)
                move_y = random.uniform(-20, 20)

            new_x = self.labubu_position.x() + move_x
            new_y = self.labubu_position.y() + move_y

            # Keep within bounds - avoid the UI area at the top (first 120 pixels)
            new_x = max(25, min(new_x, self.width() - 25))
            new_y = max(150, min(new_y, self.height() - 25))  # Start from y=150 to avoid UI

            self.labubu_position = QPoint(int(new_x), int(new_y))

        # Also add some random jittery movement
        if random.random() < 0.3:  # 30% chance
            jitter_x = random.uniform(-5, 5)
            jitter_y = random.uniform(-5, 5)

            new_x = self.labubu_position.x() + jitter_x
            new_y = self.labubu_position.y() + jitter_y

            new_x = max(25, min(new_x, self.width() - 25))
            new_y = max(150, min(new_y, self.height() - 25))  # Keep out of UI area

            self.labubu_position = QPoint(int(new_x), int(new_y))

        # Trigger repaint
        self.update()

    def show_taunt(self):
        """Show a random taunt"""
        if self.game_active:
            taunt = random.choice(self.taunts)
            self.taunt_label.setText(taunt)

    def paintEvent(self, event):
        """Paint the Labubu on the screen"""
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw Labubu as a pink circle with eyes
        labubu_rect = self.labubu_position.x() - self.labubu_size//2, self.labubu_position.y() - self.labubu_size//2, self.labubu_size, self.labubu_size

        # Main body (pink circle)
        painter.setBrush(QBrush(QColor("#FF69B4")))
        painter.setPen(QPen(QColor("#FF1493"), 2))
        painter.drawEllipse(*labubu_rect)

        # Eyes (black dots)
        eye_size = 6
        left_eye_x = self.labubu_position.x() - 10
        right_eye_x = self.labubu_position.x() + 10
        eye_y = self.labubu_position.y() - 8

        painter.setBrush(QBrush(QColor("black")))
        painter.setPen(QPen(QColor("black")))
        painter.drawEllipse(left_eye_x - eye_size//2, eye_y - eye_size//2, eye_size, eye_size)
        painter.drawEllipse(right_eye_x - eye_size//2, eye_y - eye_size//2, eye_size, eye_size)

        # Mouth (small curve)
        painter.setPen(QPen(QColor("black"), 2))
        mouth_y = self.labubu_position.y() + 5
        painter.drawArc(self.labubu_position.x() - 8, mouth_y - 4, 16, 8, 0, 180*16)

    def mousePressEvent(self, event):
        """Handle mouse clicks"""
        if not self.game_active:
            return

        self.clicks_attempted += 1

        # Check if click is on Labubu
        click_pos = event.pos()
        dx = click_pos.x() - self.labubu_position.x()
        dy = click_pos.y() - self.labubu_position.y()
        distance = math.sqrt(dx*dx + dy*dy)

        # Even if they click exactly on Labubu, it moves away at the last second!
        if distance <= self.labubu_size // 2:
            # ALMOST got it, but it escapes!
            self.taunt_label.setText("SO CLOSE! But I'm too fast! labu-labu!")

            # Jump away immediately
            jump_x = random.uniform(-100, 100)
            jump_y = random.uniform(-80, 80)

            new_x = max(25, min(self.labubu_position.x() + jump_x, self.width() - 25))
            new_y = max(150, min(self.labubu_position.y() + jump_y, self.height() - 25))  # Keep out of UI

            self.labubu_position = QPoint(int(new_x), int(new_y))
            self.update()
        else:
            # Missed click
            miss_taunts = [
                "MISSED! Try harder!",
                "Not even close!",
                "Your aim is terrible!",
                "labu-labu says TRY AGAIN!"
            ]
            self.taunt_label.setText(random.choice(miss_taunts))