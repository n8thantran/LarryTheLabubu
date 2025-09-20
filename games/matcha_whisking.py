"""Matcha Whisking Game - A modular game for the desktop pet system"""

import math
import random
import time
import os
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QLinearGradient, QRadialGradient, QPixmap, QTransform
from .base_game import BaseGame


class FoamParticle:
    def __init__(self, x, y, dx=0, dy=0):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.size = random.uniform(2, 8)
        self.life = 1.0
        self.decay_rate = random.uniform(0.005, 0.02)
        self.color = QColor(220, 255, 220, int(self.life * 100))

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.dx *= 0.98
        self.dy *= 0.98
        self.life -= self.decay_rate
        self.color.setAlpha(int(max(0, self.life * 100)))
        return self.life > 0


class MatchaWhiskingGame(BaseGame):
    def __init__(self):
        super().__init__()
        
        # Game metadata
        self.game_name = "Matcha Whisking"
        self.game_description = "Whisk matcha to the perfect consistency!"
        self.play_duration = 10  # 10 seconds
        
        self.setWindowTitle(self.game_name)
        self.setFixedSize(800, 600)
        self.setStyleSheet("background-color: #2d4a2d;")

        # Load whisk image
        self.whisk_image = self._load_whisk_image()

        # Game state
        self.liquid_level = 20.0
        self.target_level = 80.0
        self.max_level = 100.0
        self.whisking_power = 0.0
        self.game_time = 10.0
        self.start_time = None

        # Motion detection
        self.good_technique_streak = 0
        self.actual_rotation_detected = False
        self.movement_detected = False

        # Bowl properties
        self.bowl_center = QPoint(400, 350)
        self.bowl_width = 200
        self.bowl_height = 120

        # Whisking mechanics
        self.mouse_positions = []
        self.whisk_angle = 0
        self.whisk_rotation_speed = 0
        self.last_mouse_pos = QPoint()
        self.last_angle = 0
        self.whisking_speed = 0
        self.rotation_history = []
        self.speed_history = []

        # Visual effects
        self.particles = []
        self.foam_bubbles = []
        self.bowl_shake = 0
        self.liquid_animation = 0

        # Setup UI
        self.setup_ui()

        # Game loop timer (but don't start yet)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_game)
        
    def _load_whisk_image(self):
        """Load whisk image, create if doesn't exist"""
        whisk_path = "whisk.png"
        if not os.path.exists(whisk_path):
            try:
                from create_whisk_image import create_whisk_image
                create_whisk_image()
            except ImportError:
                print("create_whisk_image module not found, using fallback whisk")
                return None
        
        whisk_image = QPixmap(whisk_path)
        return whisk_image if not whisk_image.isNull() else None

    def setup_ui(self):
        layout = QVBoxLayout()

        # Header with timer and target
        header_layout = QHBoxLayout()

        self.time_label = QLabel("Time: 10s")
        self.time_label.setStyleSheet("color: #ff6b6b; font-size: 32px; font-weight: bold;")

        self.target_label = QLabel("Get to the RED LINE!")
        self.target_label.setStyleSheet("color: #ffd93d; font-size: 24px; font-weight: bold;")

        header_layout.addWidget(self.time_label)
        header_layout.addStretch()
        header_layout.addWidget(self.target_label)

        layout.addLayout(header_layout)
        layout.addStretch()

        self.setLayout(layout)
    
    def start_game(self):
        """Start the matcha whisking game"""
        self.reset_game()
        self.game_active = True
        self.start_time = time.time()
        self.timer.start(16)  # ~60 FPS
        self.setMouseTracking(True)
        print(f"Started {self.game_name}")
    
    def end_game(self):
        """End the game"""
        self.game_active = False
        self.timer.stop()
        self.setMouseTracking(False)
        print(f"Ended {self.game_name}")
    
    def is_game_finished(self):
        """Check if game is finished"""
        return self.game_won or self.game_lost
    
    def reset_game(self):
        """Reset game state"""
        super().reset_game()
        self.liquid_level = 20.0
        self.whisking_power = 0.0
        self.game_time = 10.0
        self.good_technique_streak = 0
        self.particles.clear()
        self.foam_bubbles.clear()
        self.mouse_positions.clear()
        self.rotation_history.clear()
        self.target_label.setText("Get to the RED LINE!")

    def mouseMoveEvent(self, event):
        if not self.game_active or self.game_won or self.game_lost:
            return

        current_pos = event.position().toPoint()
        self.mouse_positions.append((current_pos, time.time()))
        if len(self.mouse_positions) > 20:
            self.mouse_positions.pop(0)

        self.calculate_whisking(current_pos)
        self.last_mouse_pos = current_pos
        self.update()

    def calculate_whisking(self, current_pos):
        # Calculate distance from bowl center
        dx = current_pos.x() - self.bowl_center.x()
        dy = current_pos.y() - self.bowl_center.y()
        distance = math.sqrt(dx*dx + dy*dy)

        bowl_radius = min(self.bowl_width, self.bowl_height) / 2
        optimal_radius = bowl_radius * 0.7

        # Reset motion flags
        self.movement_detected = False
        self.actual_rotation_detected = False

        # No whisking outside bowl
        if distance > bowl_radius * 1.4:
            self.whisking_power = 0
            self.whisk_rotation_speed *= 0.9
            return

        # Calculate angle and rotation
        angle = math.atan2(dy, dx)
        angle_diff = angle - self.last_angle

        # Handle angle wrap-around
        if angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        elif angle_diff < -math.pi:
            angle_diff += 2 * math.pi

        self.rotation_history.append(angle_diff)
        if len(self.rotation_history) > 15:
            self.rotation_history.pop(0)

        # Check for actual movement
        if len(self.mouse_positions) >= 2:
            recent_pos = self.mouse_positions[-1][0]
            prev_pos = self.mouse_positions[-2][0]
            movement_dist = math.sqrt((recent_pos.x() - prev_pos.x())**2 + (recent_pos.y() - prev_pos.y())**2)
            if movement_dist > 3:
                self.movement_detected = True

        # Check for rotation
        if abs(angle_diff) > 0.04:
            self.whisk_rotation_speed = angle_diff * 8
            self.whisk_angle += self.whisk_rotation_speed
            if self.whisk_angle > 360:
                self.whisk_angle -= 360
            elif self.whisk_angle < 0:
                self.whisk_angle += 360

            if len(self.rotation_history) >= 5:
                total_rotation = sum(abs(r) for r in self.rotation_history[-5:])
                if total_rotation > 0.3:
                    self.actual_rotation_detected = True

        # Calculate speed
        if len(self.mouse_positions) >= 3:
            recent_speeds = []
            for i in range(1, min(6, len(self.mouse_positions))):
                pos1 = self.mouse_positions[i-1][0]
                pos2 = self.mouse_positions[i][0]
                time1 = self.mouse_positions[i-1][1]
                time2 = self.mouse_positions[i][1]

                dist = math.sqrt((pos2.x() - pos1.x())**2 + (pos2.y() - pos1.y())**2)
                time_diff = time2 - time1
                if time_diff > 0:
                    recent_speeds.append(dist / time_diff)

            if recent_speeds:
                self.whisking_speed = sum(recent_speeds) / len(recent_speeds)

        # No whisking power without movement and rotation
        if not self.movement_detected or not self.actual_rotation_detected:
            self.whisking_power = 0
            return

        # Must be moving fast enough
        if self.whisking_speed < 30:
            self.whisking_power = 0
            return

        # Calculate technique
        distance_score = max(0, 1 - abs(distance - optimal_radius) / (optimal_radius * 0.5))
        optimal_speed = 105
        speed_score = max(0, 1 - abs(self.whisking_speed - optimal_speed) / (optimal_speed * 0.55))

        # Circular motion consistency
        if len(self.rotation_history) >= 8:
            avg_rotation = sum(self.rotation_history) / len(self.rotation_history)
            rotation_variance = sum(abs(r - avg_rotation) for r in self.rotation_history) / len(self.rotation_history)
            rotation_consistency = max(0, 1 - rotation_variance * 4)
        else:
            rotation_consistency = 0

        # Overall technique
        overall_technique = (distance_score * 0.2 + speed_score * 0.2 + rotation_consistency * 0.6)
        self.whisking_power = overall_technique * 100

        # Track good whisking
        if overall_technique >= 0.65:
            self.good_technique_streak += 1
            # Generate particles
            if overall_technique >= 0.78 and distance < bowl_radius:
                for _ in range(min(int(overall_technique * 4), 4)):
                    px = current_pos.x() + random.uniform(-15, 15)
                    py = current_pos.y() + random.uniform(-15, 15)
                    pdx = random.uniform(-1.5, 1.5)
                    pdy = random.uniform(-3, -0.5)
                    self.particles.append(FoamParticle(px, py, pdx, pdy))

        self.last_angle = angle

    def update_game(self):
        if not self.game_active:
            return

        # Update time
        if self.start_time:
            elapsed = time.time() - self.start_time
            self.game_time = max(0, 10.0 - elapsed)

        # Check win/lose
        if self.liquid_level >= self.target_level and not self.game_won:
            self.game_won = True
            self.game_active = False
            self.target_label.setText("🏆 PERFECT MATCHA!")
            self.trigger_game_end_callback()

        elif self.game_time <= 0 and not self.game_lost and not self.game_won:
            self.game_lost = True
            self.game_active = False
            self.target_label.setText("⏰ Time's up!")
            self.trigger_game_end_callback()

        if self.game_active and not self.game_won:
            # Update liquid
            base_increase = self.whisking_power * 0.006
            streak_bonus = min(1.4, 1.0 + (self.good_technique_streak * 0.015))
            liquid_increase = base_increase * streak_bonus
            self.liquid_level = min(self.max_level, self.liquid_level + liquid_increase)

            # Liquid decay
            decay_rate = 0.04 if self.whisking_power < 35 else 0.015
            self.liquid_level = max(15, self.liquid_level - decay_rate)

        # Update effects
        self.particles = [p for p in self.particles if p.update()]

        if self.whisking_power > 55 and random.random() < 0.10:
            bubble_x = self.bowl_center.x() + random.uniform(-70, 70)
            bubble_y = self.bowl_center.y() + random.uniform(-35, 35)
            self.foam_bubbles.append({
                'x': bubble_x, 'y': bubble_y, 'size': random.uniform(4, 12),
                'life': 1.0, 'dy': random.uniform(-0.6, 0.2)
            })

        for bubble in self.foam_bubbles[:]:
            bubble['y'] += bubble['dy']
            bubble['life'] -= 0.008
            if bubble['life'] <= 0:
                self.foam_bubbles.remove(bubble)

        if self.whisking_power > 78:
            self.bowl_shake = random.uniform(-2, 2)
        else:
            self.bowl_shake *= 0.8

        self.liquid_animation = (self.liquid_animation + 0.1) % (2 * math.pi)
        self.time_label.setText(f"Time: {max(0, int(self.game_time))}s")
        self.whisk_rotation_speed *= 0.94
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background
        bg_gradient = QLinearGradient(0, 0, 0, self.height())
        bg_gradient.setColorAt(0, QColor(45, 74, 45))
        bg_gradient.setColorAt(1, QColor(20, 40, 20))
        painter.fillRect(self.rect(), QBrush(bg_gradient))

        # Bowl
        bowl_x = self.bowl_center.x() + self.bowl_shake
        bowl_y = self.bowl_center.y() + self.bowl_shake

        # Bowl shadow
        painter.setPen(QPen(QColor(0, 0, 0, 80), 4))
        painter.setBrush(QBrush(QColor(0, 0, 0, 80)))
        painter.drawEllipse(bowl_x - self.bowl_width//2 - 5, bowl_y - self.bowl_height//2 - 3,
                          self.bowl_width + 10, self.bowl_height + 6)

        # Bowl exterior
        bowl_gradient = QRadialGradient(bowl_x, bowl_y - 30, self.bowl_width//2)
        bowl_gradient.setColorAt(0, QColor(240, 240, 235))
        bowl_gradient.setColorAt(0.7, QColor(220, 220, 215))
        bowl_gradient.setColorAt(1, QColor(180, 180, 175))
        painter.setPen(QPen(QColor(160, 160, 155), 3))
        painter.setBrush(QBrush(bowl_gradient))
        painter.drawEllipse(bowl_x - self.bowl_width//2, bowl_y - self.bowl_height//2,
                          self.bowl_width, self.bowl_height)

        # Bowl interior
        interior_gradient = QRadialGradient(bowl_x, bowl_y, self.bowl_width//3)
        interior_gradient.setColorAt(0, QColor(200, 200, 195))
        interior_gradient.setColorAt(1, QColor(160, 160, 155))
        painter.setBrush(QBrush(interior_gradient))
        painter.drawEllipse(bowl_x - self.bowl_width//2 + 15, bowl_y - self.bowl_height//2 + 15,
                          self.bowl_width - 30, self.bowl_height - 30)

        # Liquid
        liquid_height_ratio = self.liquid_level / self.max_level
        liquid_height = (self.bowl_height - 30) * liquid_height_ratio

        if liquid_height > 0:
            liquid_y = bowl_y + (self.bowl_height//2 - 15) - liquid_height
            surface_wave = math.sin(self.liquid_animation * 3) * 2
            green_intensity = int(60 + (liquid_height_ratio * 120))
            matcha_color = QColor(34, min(255, green_intensity), 34)

            liquid_gradient = QLinearGradient(0, liquid_y, 0, bowl_y + self.bowl_height//2 - 15)
            liquid_gradient.setColorAt(0, matcha_color.lighter(130))
            liquid_gradient.setColorAt(1, matcha_color)

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(liquid_gradient))
            painter.drawEllipse(bowl_x - self.bowl_width//2 + 15, liquid_y + surface_wave,
                              self.bowl_width - 30, liquid_height)

        # Target line
        target_y = bowl_y + (self.bowl_height//2 - 15) - ((self.bowl_height - 30) * (self.target_level / self.max_level))
        painter.setPen(QPen(QColor(255, 100, 100), 3))
        painter.drawLine(bowl_x - self.bowl_width//2 + 20, target_y, bowl_x + self.bowl_width//2 - 20, target_y)

        # Foam bubbles
        for bubble in self.foam_bubbles:
            alpha = int(bubble['life'] * 140)
            foam_color = QColor(255, 255, 255, alpha)
            painter.setPen(QPen(foam_color, 1))
            painter.setBrush(QBrush(foam_color))
            painter.drawEllipse(bubble['x'] - bubble['size']/2, bubble['y'] - bubble['size']/2,
                              bubble['size'], bubble['size'])

        # Particles
        for particle in self.particles:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(particle.color))
            painter.drawEllipse(particle.x - particle.size/2, particle.y - particle.size/2,
                              particle.size, particle.size)

        # Whisk
        if self.game_active and not self.game_won and not self.game_lost:
            whisk_x = self.last_mouse_pos.x() if self.last_mouse_pos.x() > 0 else self.bowl_center.x()
            whisk_y = self.last_mouse_pos.y() if self.last_mouse_pos.y() > 0 else self.bowl_center.y()

            if self.whisk_image and not self.whisk_image.isNull():
                transform = QTransform()
                transform.translate(whisk_x, whisk_y)
                transform.rotate(self.whisk_angle)
                transform.translate(-50, -50)
                painter.setTransform(transform)
                painter.drawPixmap(0, 0, self.whisk_image)
                painter.resetTransform()
            else:
                # Fallback whisk
                painter.setPen(QPen(QColor(139, 69, 19), 4))
                painter.drawLine(whisk_x, whisk_y + 20, whisk_x, whisk_y - 20)
                painter.setPen(QPen(QColor(192, 192, 192), 2))
                for angle in range(0, 360, 45):
                    end_x = whisk_x + 15 * math.cos(math.radians(angle + self.whisk_angle))
                    end_y = whisk_y + 15 * math.sin(math.radians(angle + self.whisk_angle))
                    painter.drawLine(whisk_x, whisk_y, end_x, end_y)

        # Level indicator
        indicator_x = 50
        indicator_y = 200
        indicator_height = 200
        indicator_width = 22

        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.setBrush(QBrush(QColor(50, 50, 50)))
        painter.drawRect(indicator_x, indicator_y, indicator_width, indicator_height)

        current_height = int((self.liquid_level / self.max_level) * indicator_height)
        liquid_color = QColor(34, int(60 + (self.liquid_level / self.max_level) * 140), 34)
        painter.setBrush(QBrush(liquid_color))
        painter.drawRect(indicator_x, indicator_y + indicator_height - current_height,
                        indicator_width, current_height)

        # Target line on indicator
        target_height = int((self.target_level / self.max_level) * indicator_height)
        painter.setPen(QPen(QColor(255, 100, 100), 3))
        painter.drawLine(indicator_x - 5, indicator_y + indicator_height - target_height,
                        indicator_x + indicator_width + 5, indicator_y + indicator_height - target_height)

        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.setFont(QFont("Arial", 11, QFont.Bold))
        painter.drawText(indicator_x, indicator_y - 10, "LEVEL")
    
    def closeEvent(self, event):
        """Handle window close event - only close this game window"""
        print(f"🎮 Matcha Whisking game window closing...")
        
        # End game properly
        if self.game_active:
            self.end_game()
        
        # Accept the close event (only closes this window)
        event.accept()
        print("✅ Matcha Whisking game window closed - pet continues running!")


