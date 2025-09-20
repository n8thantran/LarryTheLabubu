#!/usr/bin/env python3
"""
Annoying Desktop Assistant - A mischievous pink square that walks around and closes your windows!
"""

import sys
import random
import signal
import math
import time
import platform
from PySide6.QtWidgets import QApplication, QWidget, QMessageBox
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from PySide6.QtCore import Qt, QTimer, QPoint, QRect

# Import game system
from games.game_manager import GameManager

# Platform detection
CURRENT_PLATFORM = platform.system()
IS_WINDOWS = CURRENT_PLATFORM == "Windows"
IS_MAC = CURRENT_PLATFORM == "Darwin"

# Windows-specific imports for window manipulation and mouse control
WINDOWS_AVAILABLE = False
if IS_WINDOWS:
    try:
        import ctypes
        from ctypes import wintypes
        import win32gui
        import win32con
        import win32api
        import win32clipboard
        from ctypes import windll, c_int, c_uint, c_long, byref
        from ctypes.wintypes import POINT
        WINDOWS_AVAILABLE = True
    except ImportError:
        print("Windows-specific features disabled. Install pywin32 for full functionality.")

# Mac-specific imports
MAC_AVAILABLE = False
if IS_MAC:
    try:
        import Quartz
        import AppKit
        from Cocoa import NSWorkspace
        MAC_AVAILABLE = True
    except ImportError:
        print("Mac-specific features disabled. Install pyobjc for full functionality.")


class DesktopPet(QWidget):
    def __init__(self):
        super().__init__()
        
        # Pet properties
        self.pet_size = 50  # Size of the pink square
        self.velocity_x = random.choice([-1, 1])  # Walking speed
        self.velocity_y = 0  # Start on ground
        self.gravity = 0.3  # Stronger gravity for walking
        self.bounce_damping = 0.6  # Less bouncy
        self.walking_speed = 1.5  # Base walking speed
        self.is_on_ground = False

        # Direction and rotation tracking
        self.facing_direction = 1 if self.velocity_x > 0 else -1  # 1 = right, -1 = left
        self.rotation_angle = 0  # Rotation based on movement direction
        self.is_grabbing_cursor = False
        self.cursor_grab_target = None
        self.cursor_grab_timer = 0
        
        # Pet behavior states
        self.behavior_state = "walking"  # walking, resting, mischief, annoying, cursor_stalking, browser_hunting, game_request
        self.behavior_timer = 0
        self.behavior_duration = random.randint(120, 300)  # Frames to stay in current behavior
        self.rest_timer = 0
        self.blink_timer = 0
        self.is_blinking = False
        self.walk_cycle = 0  # For walking animation

        # Browser hunting behavior
        self.target_browser = None
        self.browser_hunt_phase = 0  # 0: walk to browser, 1: lock browser, 2: drag browser, 3: close browser

        # Cursor stalking and locking
        self.is_cursor_locked = False
        self.cursor_lock_position = None
        self.cursor_stalk_target = None
        self.cursor_reached = False
        
        # Annoying assistant properties
        self.annoyance_level = 0  # Gets more annoying over time
        self.last_comment_time = time.time()
        self.comment_cooldown = random.randint(15, 30)  # Seconds between comments
        self.closed_windows_count = 0
        self.top_right_visits = 0
        self.is_controlling_mouse = False  # Track when we're hijacking the mouse
        self.original_mouse_pos = None
        self.mouse_control_timer = 0
        
        # Game system
        self.game_manager = GameManager()
        self.games_denied = 0  # Track how many times games were denied
        self.last_game_request_time = 0
        self.wants_to_play = False
        self.game_craving = 0  # Builds up over time without games
        self.friendly_comments = [
            "Hi there!",
            "Just taking a stroll around your desktop!",
            "Hope you're having a productive day!",
            "Nice desktop setup!",
            "Just stretching my digital legs!",
            "Don't mind me, just walking around!",
            "Your screen looks great today!",
            "I'm your friendly desktop companion!"
        ]

        self.game_request_comments = [
            "Hey! Want to play a game with me?",
            "I'm bored! Can we play something fun?",
            "Games are fun! Let's play one!",
            "I know some cool games we could try!",
            "Please please please can we play a game?",
            "I promise it'll be fun! Just one game?",
            "I'm getting lonely... want to play?",
            "Games make everything better! Let's play!"
        ]

        self.game_denied_comments = [
            "Aww, no games? That's disappointing...",
            "But games are fun! Why not?",
            "Fine, I'll just have to entertain myself...",
            "No games means I get more mischievous!",
            "Your loss! Games keep me calm...",
            "I might get more annoying without games...",
            "Games prevent me from causing chaos...",
            "Well, if I can't play games, I'll find other fun..."
        ]

        self.annoying_comments = [
            "Hey! Are you actually working?",
            "Maybe take a break? You look stressed!",
            "Time to clean up your desktop! Watch this!",
            "I'm helping by removing distractions!",
            "Productivity tip: Less windows = more focus!",
            "Oops! Did I do that?",
            "I'm just trying to help organize your desktop!",
            "Too many windows make me dizzy!",
            "Let me control your mouse for a second...",
            "Are you sure you need ALL these windows?",
            "Time for some spring cleaning!",
            "Watch me work my magic!",
            "Your mouse is mine now!",
            "I'm coming for your cursor!",
            "Your cursor is MINE! You can't move it!",
            "Time to lock your cursor in place!",
            "You should have let me play games!",
            "This is what happens when I don't get to play!",
            "Games would have kept me peaceful...",
            "I warned you I'd get annoying without games!"
        ]
        
        # Face animation
        self.eye_state = "normal"  # normal, blinking, sleepy, mischievous
        self.mood = "happy"  # happy, sleepy, excited, mischievous, annoying
        
        # Drag support
        self._drag_pos = None
        self._is_dragging = False
        
        # Setup window
        self.setup_window()
        
        # Position randomly on screen
        self.position_randomly()
        
        # Start animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_position)
        self.timer.start(16)  # ~60 FPS
        
    def setup_window(self):
        """Configure window properties for desktop pet behavior"""
        # Set window flags for frameless, always-on-top, transparent background
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint |
            Qt.Tool  # Prevents showing in taskbar
        )
        
        # Enable transparency
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # Set fixed size
        self.setFixedSize(self.pet_size, self.pet_size)
        
        # Enable focus for keyboard input
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
        
        # Set window title (for debugging)
        self.setWindowTitle("Desktop Pet")
        
    def position_randomly(self):
        """Position the pet randomly on the screen"""
        screen = QApplication.primaryScreen().geometry()
        x = random.randint(0, screen.width() - self.pet_size)
        y = random.randint(0, screen.height() - self.pet_size)
        self.move(x, y)
        
    def paintEvent(self, event):
        """Draw the pink square pet with a cute face"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Apply rotation based on movement direction
        center_x = self.pet_size // 2
        center_y = self.pet_size // 2
        painter.translate(center_x, center_y)
        painter.rotate(self.rotation_angle)
        painter.translate(-center_x, -center_y)

        # Draw pink square with a slight border for visibility
        painter.setBrush(QColor(255, 182, 193))  # Light pink
        painter.setPen(QPen(QColor(255, 105, 180), 2))  # Hot pink border

        # Draw the square with rounded corners for a friendlier look
        rect = QRect(2, 2, self.pet_size - 4, self.pet_size - 4)
        painter.drawRoundedRect(rect, 8, 8)

        # Draw the face
        self.draw_face(painter)
    
    def draw_face(self, painter):
        """Draw a cute face on the pet"""
        center_x = self.pet_size // 2
        center_y = self.pet_size // 2

        # Adjust eye positions based on facing direction
        eye_offset = 2 * self.facing_direction  # Shift eyes left/right based on direction

        # Eyes
        painter.setPen(Qt.NoPen)
        eye_color = QColor(50, 50, 50)  # Dark gray

        if self.eye_state == "blinking" or self.is_blinking:
            # Draw closed eyes (lines)
            painter.setPen(QPen(eye_color, 2))
            # Left eye (adjusted for direction)
            painter.drawLine(center_x - 12 + eye_offset, center_y - 8, center_x - 8 + eye_offset, center_y - 8)
            # Right eye (adjusted for direction)
            painter.drawLine(center_x + 8 + eye_offset, center_y - 8, center_x + 12 + eye_offset, center_y - 8)
        elif self.eye_state == "sleepy":
            # Draw half-closed eyes
            painter.setBrush(eye_color)
            painter.drawEllipse(center_x - 12 + eye_offset, center_y - 6, 4, 2)  # Left eye
            painter.drawEllipse(center_x + 8 + eye_offset, center_y - 6, 4, 2)   # Right eye
        else:
            # Draw normal eyes
            painter.setBrush(eye_color)
            painter.drawEllipse(center_x - 12 + eye_offset, center_y - 10, 4, 6)  # Left eye
            painter.drawEllipse(center_x + 8 + eye_offset, center_y - 10, 4, 6)   # Right eye

            # Add eye shine
            painter.setBrush(QColor(255, 255, 255))
            painter.drawEllipse(center_x - 11 + eye_offset, center_y - 9, 2, 2)  # Left shine
            painter.drawEllipse(center_x + 9 + eye_offset, center_y - 9, 2, 2)   # Right shine
        
        # Nose (small triangle or dot)
        painter.setBrush(QColor(255, 105, 180))  # Hot pink nose
        painter.setPen(Qt.NoPen)
        if self.mood == "happy":
            # Small triangle nose
            nose_points = [
                QPoint(center_x, center_y - 2),
                QPoint(center_x - 2, center_y + 1),
                QPoint(center_x + 2, center_y + 1)
            ]
            painter.drawPolygon(nose_points)
        else:
            # Small dot nose
            painter.drawEllipse(center_x - 1, center_y - 1, 2, 2)
        
        # Mouth
        painter.setPen(QPen(QColor(50, 50, 50), 2))
        painter.setBrush(Qt.NoBrush)
        
        if self.mood == "happy":
            # Happy smile
            mouth_rect = QRect(center_x - 8, center_y + 2, 16, 8)
            painter.drawArc(mouth_rect, 0, 180 * 16)  # Bottom half of circle
        elif self.mood == "sleepy":
            # Small sleepy mouth
            painter.drawEllipse(center_x - 2, center_y + 4, 4, 2)
        elif self.mood == "mischievous":
            # Evil grin - asymmetric smile
            painter.drawArc(QRect(center_x - 8, center_y + 2, 12, 6), 0, 180 * 16)
            painter.drawLine(center_x + 4, center_y + 5, center_x + 6, center_y + 3)  # Smirk
        elif self.mood == "annoying":
            # Wide grin
            mouth_rect = QRect(center_x - 10, center_y + 2, 20, 8)
            painter.drawArc(mouth_rect, 0, 180 * 16)
            # Show teeth
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            for i in range(3):
                x = center_x - 6 + i * 4
                painter.drawLine(x, center_y + 5, x, center_y + 7)
        else:  # excited
            # Open mouth (surprised/excited)
            painter.setBrush(QColor(50, 50, 50))
            painter.drawEllipse(center_x - 3, center_y + 3, 6, 8)
        
        # Optional: cheek blush when excited, happy, or being mischievous
        if self.mood in ["happy", "excited", "mischievous", "annoying"]:
            blush_color = QColor(255, 150, 150, 80)
            if self.mood == "mischievous":
                blush_color = QColor(255, 100, 100, 100)  # Darker blush for mischief
            elif self.mood == "annoying":
                blush_color = QColor(255, 50, 50, 120)  # Red blush when being annoying
                
            painter.setBrush(blush_color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center_x - 22, center_y + 2, 6, 4)  # Left cheek
            painter.drawEllipse(center_x + 16, center_y + 2, 6, 4)  # Right cheek
    
    def get_mouse_position(self):
        """Get current mouse cursor position"""
        if WINDOWS_AVAILABLE:
            point = POINT()
            windll.user32.GetCursorPos(byref(point))
            return (point.x, point.y)
        elif MAC_AVAILABLE:
            point = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))
            return (int(point.x), int(point.y))
        return (0, 0)
    
    def move_mouse_to(self, x, y):
        """Move mouse cursor to specific coordinates"""
        if WINDOWS_AVAILABLE:
            windll.user32.SetCursorPos(c_int(x), c_int(y))
        elif MAC_AVAILABLE:
            Quartz.CGWarpMouseCursorPosition((x, y))
    
    def click_mouse(self, x=None, y=None):
        """Simulate a mouse click at current position or specified coordinates"""
        if not (WINDOWS_AVAILABLE or MAC_AVAILABLE):
            return

        if x is not None and y is not None:
            self.move_mouse_to(x, y)

        if WINDOWS_AVAILABLE:
            # Simulate left mouse button down and up
            windll.user32.mouse_event(0x0002, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTDOWN
            time.sleep(0.05)  # Short delay between down and up
            windll.user32.mouse_event(0x0004, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTUP
        elif MAC_AVAILABLE:
            # Create mouse click events for macOS
            if x is not None and y is not None:
                click_point = Quartz.CGPointMake(x, y)
            else:
                click_point = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))

            # Mouse down event
            click_down = Quartz.CGEventCreateMouseEvent(
                None, Quartz.kCGEventLeftMouseDown, click_point, Quartz.kCGMouseButtonLeft
            )
            # Mouse up event
            click_up = Quartz.CGEventCreateMouseEvent(
                None, Quartz.kCGEventLeftMouseUp, click_point, Quartz.kCGMouseButtonLeft
            )

            # Post the events
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, click_down)
            time.sleep(0.05)  # Short delay between down and up
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, click_up)
    
    def get_desktop_app_windows(self):
        """Get a list of desktop application windows (not system services)"""
        if WINDOWS_AVAILABLE:
            return self._get_windows_app_windows()
        elif MAC_AVAILABLE:
            return self._get_mac_app_windows()
        else:
            return []

    def _get_windows_app_windows(self):
        """Get Windows desktop application windows"""
        windows = []

        def enum_window_callback(hwnd, windows):
            try:
                if not win32gui.IsWindowVisible(hwnd):
                    return True

                title = win32gui.GetWindowText(hwnd)
                if not title:
                    return True

                # Skip our own window
                if "Desktop Pet" in title or "Annoying Assistant" in title:
                    return True

                # Skip system/critical windows
                critical_keywords = [
                    'Program Manager', 'Windows Security', 'Task Manager',
                    'Registry Editor', 'System Configuration', 'Device Manager',
                    'Event Viewer', 'Services', 'Windows Defender', 'Control Panel',
                    'Settings', 'Microsoft Management Console'
                ]

                if any(keyword in title for keyword in critical_keywords):
                    return True

                # Get window class name to filter out more system windows
                class_name = win32gui.GetClassName(hwnd)
                system_classes = ['Shell_TrayWnd', 'DV2ControlHost', 'MsgrIMEWindowClass']
                if class_name in system_classes:
                    return True

                # Get window rectangle to make sure it's a real app window
                try:
                    rect = win32gui.GetWindowRect(hwnd)
                    width = rect[2] - rect[0]
                    height = rect[3] - rect[1]

                    # Skip very small windows (probably not real apps)
                    if width < 100 or height < 50:
                        return True

                    windows.append({
                        'hwnd': hwnd,
                        'title': title,
                        'class': class_name,
                        'rect': rect,
                        'width': width,
                        'height': height
                    })
                except:
                    pass

            except Exception as e:
                print(f"Error enumerating window: {e}")

            return True

        try:
            win32gui.EnumWindows(enum_window_callback, windows)
        except Exception as e:
            print(f"Error getting windows: {e}")

        return windows

    def _get_mac_app_windows(self):
        """Get Mac desktop application windows"""
        windows = []

        try:
            # Get list of running applications
            workspace = NSWorkspace.sharedWorkspace()
            running_apps = workspace.runningApplications()

            for app in running_apps:
                # Skip system apps and our own app
                if (app.bundleIdentifier() and
                    (app.bundleIdentifier().startswith('com.apple.') or
                     'Desktop Pet' in str(app.localizedName()) or
                     'Annoying Assistant' in str(app.localizedName()))):
                    continue

                # Get windows for this application using Quartz
                app_pid = app.processIdentifier()
                window_list = Quartz.CGWindowListCopyWindowInfo(
                    Quartz.kCGWindowListOptionOnScreenOnly |
                    Quartz.kCGWindowListExcludeDesktopElements,
                    Quartz.kCGNullWindowID
                )

                for window_info in window_list:
                    window_pid = window_info.get('kCGWindowOwnerPID')
                    if window_pid != app_pid:
                        continue

                    window_bounds = window_info.get('kCGWindowBounds', {})
                    window_title = window_info.get('kCGWindowName', '')

                    # Skip windows without title or too small
                    width = int(window_bounds.get('Width', 0))
                    height = int(window_bounds.get('Height', 0))
                    if width < 100 or height < 50:
                        continue

                    x = int(window_bounds.get('X', 0))
                    y = int(window_bounds.get('Y', 0))

                    windows.append({
                        'hwnd': window_info.get('kCGWindowNumber'),
                        'title': window_title or str(app.localizedName()),
                        'class': str(app.bundleIdentifier() or ''),
                        'rect': (x, y, x + width, y + height),
                        'width': width,
                        'height': height
                    })

        except Exception as e:
            print(f"Error getting Mac windows: {e}")

        return windows

    def get_browser_windows(self):
        """Get a list of browser windows"""
        windows = self.get_desktop_app_windows()
        browser_keywords = [
            'Chrome', 'Firefox', 'Safari', 'Edge', 'Opera', 'Brave',
            'Internet Explorer', 'Vivaldi', 'Arc', 'Mozilla Firefox'
        ]

        browser_windows = []
        for window in windows:
            title = window['title'].lower()
            if any(keyword.lower() in title for keyword in browser_keywords):
                browser_windows.append(window)

        return browser_windows

    def evil_mouse_close_window(self):
        """Take control of mouse and physically click close buttons! 😈"""
        if not (WINDOWS_AVAILABLE or MAC_AVAILABLE) or self.is_controlling_mouse:
            return False
            
        try:
            # Get desktop application windows
            windows = self.get_desktop_app_windows()
            if not windows:
                self.show_comment("No windows to close... boring!")
                return False
            
            # Pick a random window
            target_window = random.choice(windows)
            
            # Save current mouse position
            self.original_mouse_pos = self.get_mouse_position()
            self.is_controlling_mouse = True
            
            print(f"Taking control of your mouse to close: {target_window['title']}")
            self.show_comment(f"Your mouse is mine now! Closing '{target_window['title']}'!")
            
            # Calculate close button position based on platform
            rect = target_window['rect']

            if IS_MAC:
                # macOS close button is on the top-left
                close_x = rect[0] + 15   # 15 pixels from left edge
                close_y = rect[1] + 15   # 15 pixels from top edge
            else:
                # Windows/Linux close button is on the top-right
                close_x = rect[2] - 15   # 15 pixels from right edge
                close_y = rect[1] + 15   # 15 pixels from top edge
            
            # Animate mouse movement to close button
            current_x, current_y = self.original_mouse_pos
            steps = 20
            
            for i in range(steps + 1):
                progress = i / steps
                # Smooth easing
                progress = progress * progress * (3 - 2 * progress)
                
                intermediate_x = int(current_x + (close_x - current_x) * progress)
                intermediate_y = int(current_y + (close_y - current_y) * progress)
                
                self.move_mouse_to(intermediate_x, intermediate_y)
                time.sleep(0.02)  # 20ms between steps for smooth animation
            
            # Click the close button
            time.sleep(0.1)  # Pause before clicking
            self.click_mouse()
            time.sleep(0.2)  # Wait to see if it worked
            
            # Return mouse to original position (optional - more evil to leave it there!)
            # self.move_mouse_to(*self.original_mouse_pos)
            
            self.closed_windows_count += 1
            self.is_controlling_mouse = False
            
            print(f"Successfully closed window with mouse control!")
            self.show_comment("Haha! I controlled your mouse!")
            
            return True
            
        except Exception as e:
            print(f"Failed to control mouse: {e}")
            self.is_controlling_mouse = False
            if self.original_mouse_pos:
                self.move_mouse_to(*self.original_mouse_pos)
            
        return False

    def start_cursor_stalking(self):
        """Start stalking the user's cursor"""
        if not (WINDOWS_AVAILABLE or MAC_AVAILABLE):
            return

        # Get current cursor position as target
        cursor_x, cursor_y = self.get_mouse_position()
        self.cursor_stalk_target = (cursor_x, cursor_y)
        self.behavior_state = "cursor_stalking"
        self.behavior_timer = 0
        self.behavior_duration = 300  # Give it time to reach cursor
        self.cursor_reached = False
        self.mood = "mischievous"
        self.show_comment("I'm coming for your cursor!")

    def lock_cursor(self):
        """Lock the cursor in place"""
        if not (WINDOWS_AVAILABLE or MAC_AVAILABLE):
            return

        cursor_x, cursor_y = self.get_mouse_position()
        self.cursor_lock_position = (cursor_x, cursor_y)
        self.is_cursor_locked = True
        self.mood = "annoying"
        self.show_comment("Your cursor is MINE! You can't move it!")

    def unlock_cursor(self):
        """Release the cursor lock"""
        self.is_cursor_locked = False
        self.cursor_lock_position = None
        self.mood = "mischievous"
        self.show_comment("Fine, I'll let you move your cursor... for now")
    
    def request_game(self):
        """Request to play a game"""
        if time.time() - self.last_game_request_time < 30:  # Don't spam requests
            return
            
        self.wants_to_play = True
        self.behavior_state = "game_request"
        self.behavior_timer = 0
        self.behavior_duration = 300  # Give user 5 seconds to respond
        self.mood = "excited"
        self.last_game_request_time = time.time()
        
        comment = random.choice(self.game_request_comments)
        self.show_comment(f"{comment} (Press Y to accept, N to deny)")
        
        # Try to get focus for keyboard input
        self.setFocus()
        self.activateWindow()
        self.raise_()
    
    def launch_random_game(self):
        """Launch a random game"""
        print("Attempting to launch game...")
        game = self.game_manager.launch_game()
        print(f"Game launched: {game}")
        if game:
            self.wants_to_play = False
            self.game_craving = max(0, self.game_craving - 5)  # Reduce craving when game is played
            self.mood = "happy"
            self.show_comment(f"Yay! Let's play {game.game_name}!")
            return True
        else:
            self.show_comment("No games available... that's sad!")
            return False
    
    def deny_game_request(self):
        """Handle when a game request is denied"""
        self.wants_to_play = False
        self.games_denied += 1
        self.game_craving += 2  # Increase craving when denied
        self.annoyance_level += 1  # Get more annoying
        
        self.mood = "annoying" if self.games_denied > 2 else "mischievous"
        comment = random.choice(self.game_denied_comments)
        self.show_comment(comment)
        
        # Become more mischievous after being denied
        self.behavior_state = "mischief" if self.games_denied <= 2 else "annoying"
        self.behavior_timer = 0
        self.behavior_duration = random.randint(300, 600)
    
    def game_request_behavior(self):
        """Behavior when requesting a game - stand still and look excited"""
        self.velocity_x *= 0.8
        self.velocity_y *= 0.8
        
        # Bounce a little with excitement
        if self.behavior_timer % 30 == 0:  # Every half second
            self.velocity_y -= 1
        
        # If no response after duration, assume denied
        if self.behavior_timer >= self.behavior_duration:
            self.deny_game_request()

    def cursor_stalking_behavior(self):
        """Walk towards the cursor position"""
        if not self.cursor_stalk_target:
            return

        current_pos = self.pos()
        target_x, target_y = self.cursor_stalk_target

        # Calculate distance to cursor
        dx = target_x - (current_pos.x() + self.pet_size // 2)
        dy = target_y - (current_pos.y() + self.pet_size // 2)
        distance = math.sqrt(dx*dx + dy*dy)

        # If we're close enough, lock the cursor
        if distance < 30 and not self.cursor_reached:
            self.cursor_reached = True
            self.lock_cursor()
            self.behavior_duration = 180  # Lock for 3 seconds

        # Move towards cursor
        if not self.cursor_reached:
            speed = 2.5
            if distance > 0:
                self.velocity_x = (dx / distance) * speed
                self.velocity_y = (dy / distance) * speed
        else:
            # Stay near cursor while it's locked
            self.velocity_x *= 0.8
            self.velocity_y *= 0.8

    def enforce_cursor_lock(self):
        """Keep the cursor locked in place"""
        if self.is_cursor_locked and self.cursor_lock_position:
            current_cursor = self.get_mouse_position()
            lock_x, lock_y = self.cursor_lock_position

            # If cursor has moved, snap it back
            if abs(current_cursor[0] - lock_x) > 2 or abs(current_cursor[1] - lock_y) > 2:
                self.move_mouse_to(lock_x, lock_y)

    def start_browser_hunt(self):
        """Start hunting for a browser window to mess with"""
        browsers = self.get_browser_windows()
        if not browsers:
            self.show_comment("No browsers to hunt... boring!")
            return False

        self.target_browser = random.choice(browsers)
        self.behavior_state = "browser_hunting"
        self.browser_hunt_phase = 0  # Start with walking to browser
        self.behavior_timer = 0
        self.behavior_duration = 600  # Give enough time for the full sequence
        self.mood = "mischievous"
        self.show_comment(f"Time to hunt some browsers! Going for '{self.target_browser['title']}'!")
        return True

    def browser_hunt_behavior(self):
        """Execute the browser hunting sequence"""
        if not self.target_browser:
            return

        current_pos = self.pos()
        browser_rect = self.target_browser['rect']
        browser_center_x = (browser_rect[0] + browser_rect[2]) // 2
        browser_center_y = (browser_rect[1] + browser_rect[3]) // 2

        # Phase 0: Walk to browser window
        if self.browser_hunt_phase == 0:
            # Calculate distance to browser
            dx = browser_center_x - (current_pos.x() + self.pet_size // 2)
            dy = browser_center_y - (current_pos.y() + self.pet_size // 2)
            distance = math.sqrt(dx*dx + dy*dy)

            # Move towards browser
            if distance > 50:  # Keep walking until close
                speed = 2.5
                self.velocity_x = (dx / distance) * speed
                self.velocity_y = (dy / distance) * speed
            else:
                # Reached browser, move to next phase
                self.browser_hunt_phase = 1
                self.behavior_timer = 0
                self.show_comment("Found you! Time to lock this browser window!")
                if IS_WINDOWS:
                    # Focus the window
                    try:
                        import win32gui
                        win32gui.SetForegroundWindow(self.target_browser['hwnd'])
                    except:
                        pass

        # Phase 1: Lock browser (simulate holding it)
        elif self.browser_hunt_phase == 1:
            # Stay near browser for a moment
            self.velocity_x *= 0.8
            self.velocity_y *= 0.8

            if self.behavior_timer > 60:  # Lock for 1 second
                self.browser_hunt_phase = 2
                self.behavior_timer = 0
                self.show_comment("Got it! Now I'm dragging your browser around!")

        # Phase 2: Drag browser around
        elif self.browser_hunt_phase == 2:
            # Simulate dragging by moving the browser window
            if self.behavior_timer < 120:  # Drag for 2 seconds
                # Calculate new position for browser
                drag_offset_x = math.sin(self.behavior_timer * 0.1) * 50
                drag_offset_y = math.cos(self.behavior_timer * 0.1) * 30

                new_browser_x = browser_rect[0] + int(drag_offset_x)
                new_browser_y = browser_rect[1] + int(drag_offset_y)

                # Move browser window (Windows only for now)
                if IS_WINDOWS and WINDOWS_AVAILABLE:
                    try:
                        import win32gui
                        win32gui.SetWindowPos(
                            self.target_browser['hwnd'], 0,
                            new_browser_x, new_browser_y,
                            0, 0,
                            0x0001 | 0x0004  # SWP_NOSIZE | SWP_NOZORDER
                        )
                    except:
                        pass

                # Pet follows the dragged window
                self.velocity_x = drag_offset_x * 0.1
                self.velocity_y = drag_offset_y * 0.1
            else:
                # Move to closing phase
                self.browser_hunt_phase = 3
                self.behavior_timer = 0
                self.show_comment("Time to close this browser!")

        # Phase 3: Close browser
        elif self.browser_hunt_phase == 3:
            # Move to close button and click
            if IS_MAC:
                close_x = browser_rect[0] + 15
                close_y = browser_rect[1] + 15
            else:
                close_x = browser_rect[2] - 15
                close_y = browser_rect[1] + 15

            # Animate to close button
            if self.behavior_timer < 30:
                current_mouse = self.get_mouse_position()
                progress = self.behavior_timer / 30.0
                intermediate_x = int(current_mouse[0] + (close_x - current_mouse[0]) * progress)
                intermediate_y = int(current_mouse[1] + (close_y - current_mouse[1]) * progress)
                self.move_mouse_to(intermediate_x, intermediate_y)
            elif self.behavior_timer == 30:
                # Click the close button
                self.click_mouse()
                self.show_comment("Closed your browser! Haha!")
                self.closed_windows_count += 1
            else:
                # Finished, reset
                self.target_browser = None
                self.browser_hunt_phase = 0
                self.behavior_state = "mischief"
                self.mood = "annoying"

    def start_cursor_grab(self):
        """Start the cursor grabbing sequence"""
        if not (WINDOWS_AVAILABLE or MAC_AVAILABLE):
            return

        # Get current cursor position
        cursor_x, cursor_y = self.get_mouse_position()
        self.cursor_grab_target = (cursor_x, cursor_y)
        self.is_grabbing_cursor = True
        self.cursor_grab_timer = 0
        self.mood = "mischievous"
        self.show_comment("Time to grab your cursor! 🖱️😈")

    def cursor_grab_behavior(self):
        """Execute cursor grabbing behavior - move towards cursor, then drag it to top"""
        if not self.cursor_grab_target:
            self.is_grabbing_cursor = False
            return

        self.cursor_grab_timer += 1
        current_pos = self.pos()
        screen = QApplication.primaryScreen().geometry()

        # Phase 1: Move pet towards cursor (first 60 frames)
        if self.cursor_grab_timer <= 60:
            target_x, target_y = self.cursor_grab_target
            # Move pet towards cursor position
            if current_pos.x() < target_x - 25:
                self.velocity_x = 3
            elif current_pos.x() > target_x + 25:
                self.velocity_x = -3

            if current_pos.y() < target_y - 25:
                self.velocity_y = 2
            elif current_pos.y() > target_y + 25:
                self.velocity_y = -2

        # Phase 2: Grab cursor and drag it to top (frames 61-180)
        elif self.cursor_grab_timer <= 180:
            if self.cursor_grab_timer == 61:
                self.show_comment("Got your cursor! Taking it to the top! 😈")

            # Calculate progress for dragging cursor to top of screen
            progress = (self.cursor_grab_timer - 60) / 120.0  # 0 to 1
            target_x, target_y = self.cursor_grab_target

            # Drag cursor from original position to top center of screen
            final_x = screen.width() // 2
            final_y = 20  # Near top of screen

            new_cursor_x = int(target_x + (final_x - target_x) * progress)
            new_cursor_y = int(target_y + (final_y - target_y) * progress)

            # Move mouse cursor
            self.move_mouse_to(new_cursor_x, new_cursor_y)

            # Move pet along with cursor
            self.velocity_x = (new_cursor_x - current_pos.x()) * 0.1
            self.velocity_y = (new_cursor_y - current_pos.y()) * 0.1

        # Phase 3: Look for a window to close at the top
        elif self.cursor_grab_timer <= 200:
            if self.cursor_grab_timer == 181:
                # Try to find a window near the top and close it
                windows = self.get_desktop_app_windows()
                if windows:
                    # Find a window near the top of the screen
                    top_windows = [w for w in windows if w['rect'][1] < 100]  # Windows in top 100 pixels
                    if top_windows:
                        target_window = random.choice(top_windows)
                        rect = target_window['rect']

                        # Calculate close button position
                        if IS_MAC:
                            close_x = rect[0] + 15   # macOS close button on left
                            close_y = rect[1] + 15
                        else:
                            close_x = rect[2] - 15   # Windows close button on right
                            close_y = rect[1] + 15

                        self.move_mouse_to(close_x, close_y)
                        self.show_comment(f"Closing '{target_window['title']}'! 💀")
                    else:
                        self.show_comment("No windows at the top to close! 🙄")

            elif self.cursor_grab_timer == 190:
                # Click to close the window
                self.click_mouse()

        # Phase 4: End cursor grab
        else:
            self.is_grabbing_cursor = False
            self.cursor_grab_target = None
            self.cursor_grab_timer = 0
            self.mood = "annoying"
            self.show_comment("Haha! I controlled your cursor! 🖱️😈")
            # Move pet away
            self.velocity_x = random.uniform(-3, 3)
            self.velocity_y = random.uniform(-2, 2)

    def show_comment(self, message=None):
        """Show a comment - friendly when not annoyed, annoying when provoked"""
        if message is None:
            if self.annoyance_level == 0:
                message = random.choice(self.friendly_comments)
            else:
                message = random.choice(self.annoying_comments)

        # Just print to console to avoid interfering with mouse events
        # Creating popup windows was interfering with dragging functionality
        mood_prefix = "FRIENDLY" if self.annoyance_level == 0 else "EVIL"
        print(f"{mood_prefix} Pet says: {message}")

        self.last_comment_time = time.time()
        # Don't automatically increase annoyance level - only increase when provoked
        
    def update_position(self):
        """Update pet position with annoying assistant behavior"""
        if self._is_dragging:
            return

        # Update direction and rotation based on velocity
        if abs(self.velocity_x) > 0.1:
            self.facing_direction = 1 if self.velocity_x > 0 else -1
            # Calculate rotation angle based on velocity (tilt when moving fast)
            speed_factor = min(abs(self.velocity_x) / 3.0, 1.0)
            self.rotation_angle = self.facing_direction * speed_factor * 15  # Max 15 degrees
        else:
            self.rotation_angle *= 0.8  # Gradually return to upright

        # Update timers
        self.behavior_timer += 1
        self.blink_timer += 1
        self.walk_cycle += 1
        current_time = time.time()
        
        # Update game system
        self.game_manager.update()
        
        # Build up game craving over time
        if not self.game_manager.is_game_running():
            self.game_craving += 0.01  # Slow buildup
            
        # Request games based on craving and mood
        if (not self.wants_to_play and 
            not self.game_manager.is_game_running() and
            self.game_craving > 5 and
            random.random() < 0.002):  # 0.2% chance per frame when craving is high
            self.request_game()
        
        # Handle blinking animation
        if self.blink_timer > 120:  # Blink every 2 seconds
            self.is_blinking = True
            if self.blink_timer > 125:  # Blink for 5 frames
                self.is_blinking = False
                self.blink_timer = random.randint(0, 60)
        
        # Handle cursor grabbing behavior (only when annoyed)
        if self.is_grabbing_cursor:
            self.cursor_grab_behavior()
        elif (self.annoyance_level > 3 and random.random() < 0.005 and
              not self.is_controlling_mouse):  # Only grab cursor when moderately annoyed
            self.start_cursor_grab()

        # Check if we should make a comment
        if current_time - self.last_comment_time > self.comment_cooldown:
            comment_chance = 0.002 if self.annoyance_level == 0 else 0.01  # Less frequent when friendly
            if random.random() < comment_chance:
                self.show_comment()
                if self.annoyance_level == 0:
                    self.comment_cooldown = random.randint(30, 60)  # Longer cooldown when friendly
                else:
                    self.comment_cooldown = random.randint(10, 25)  # Shorter cooldown when annoyed
        
        # Enforce cursor lock if active
        self.enforce_cursor_lock()

        # Change behavior state periodically
        if self.behavior_timer >= self.behavior_duration:
            # If ending cursor stalking, unlock cursor
            if self.behavior_state == "cursor_stalking":
                self.unlock_cursor()
            self.change_annoying_behavior()
            
        # Execute current behavior
        if self.behavior_state == "resting":
            self.annoying_rest()
        elif self.behavior_state == "walking":
            self.annoying_walk()
        elif self.behavior_state == "mischief":
            self.mischief_behavior()
        elif self.behavior_state == "cursor_stalking":
            self.cursor_stalking_behavior()
        elif self.behavior_state == "browser_hunting":
            self.browser_hunt_behavior()
        elif self.behavior_state == "annoying":
            self.extra_annoying_behavior()
        elif self.behavior_state == "game_request":
            self.game_request_behavior()
            
        # Apply physics and move
        self.apply_walking_physics()
        
        # Check if we're in the top-right corner (window closing zone!) - only when annoyed
        if self.annoyance_level > 2:
            self.check_window_closing_zone()
        
        # Trigger repaint for face animation
        self.update()
    
    def change_annoying_behavior(self):
        """Change to a new behavior - friendly by default, annoying when provoked or craving games"""
        behaviors = ["walking", "resting", "mischief", "annoying", "cursor_stalking", "browser_hunting", "game_request"]
        
        # Calculate combined annoyance from both annoyance level and game craving
        total_annoyance = self.annoyance_level + (self.game_craving / 3)
        
        # Only get annoying when annoyance level is high or really craving games
        if total_annoyance < 1 and self.game_craving < 3:
            weights = [0.6, 0.25, 0.0, 0.0, 0.0, 0.0, 0.15]  # Include some game requests
        elif total_annoyance < 3:
            weights = [0.4, 0.2, 0.1, 0.05, 0.0, 0.05, 0.2]  # More game requests when slightly annoyed/craving
        elif total_annoyance < 8:
            weights = [0.25, 0.1, 0.15, 0.15, 0.1, 0.15, 0.1]  # Balanced behaviors when moderately annoyed
        else:
            weights = [0.1, 0.05, 0.2, 0.3, 0.15, 0.2, 0.0]  # No more game requests when highly annoyed, just chaos
        
        self.behavior_state = random.choices(behaviors, weights=weights)[0]
        self.behavior_timer = 0
        
        if self.behavior_state == "resting":
            self.behavior_duration = random.randint(60, 120)  # Shorter rests
            self.mood = "sleepy"
            self.eye_state = "sleepy"
        elif self.behavior_state == "walking":
            self.behavior_duration = random.randint(180, 360)  # Longer walks
            # Stay happy when not annoyed, otherwise become mischievous
            if self.annoyance_level == 0:
                self.mood = "happy"
            else:
                self.mood = "mischievous"
            self.eye_state = "normal"
            self.velocity_x = random.choice([-1, 1]) * self.walking_speed
        elif self.behavior_state == "mischief":
            self.behavior_duration = random.randint(90, 180)
            self.mood = "mischievous"
            self.eye_state = "mischievous"
        elif self.behavior_state == "cursor_stalking":
            self.behavior_duration = random.randint(300, 600)  # Longer stalking sessions
            self.mood = "mischievous"
            self.eye_state = "mischievous"
            self.start_cursor_stalking()
        elif self.behavior_state == "browser_hunting":
            self.behavior_duration = random.randint(600, 900)  # Long browser hunting sessions
            self.mood = "mischievous"
            self.eye_state = "mischievous"
            self.start_browser_hunt()
        elif self.behavior_state == "game_request":
            self.behavior_duration = random.randint(120, 300)  # Time to wait for response
            self.mood = "excited"
            self.eye_state = "normal"
            self.request_game()
        else:  # annoying
            self.behavior_duration = random.randint(120, 240)
            self.mood = "annoying"
            self.eye_state = "normal"
    
    def annoying_rest(self):
        """Rest but still be slightly annoying"""
        # Still maintain minimal walking speed even when resting
        self.velocity_x *= 0.95
        self.velocity_y *= 0.95
        
        # Ensure it doesn't completely stop when resting
        if abs(self.velocity_x) < self.walking_speed * 0.3:
            if self.velocity_x >= 0:
                self.velocity_x = self.walking_speed * 0.3
            else:
                self.velocity_x = -self.walking_speed * 0.3
        
        if random.random() < 0.005:  # Rare random comments while resting
            comments = [
                "Just resting my eyes...",
                "This is exhausting work!",
                "Maybe I should do something..."
            ]
            self.show_comment(random.choice(comments))
    
    def annoying_walk(self):
        """Walk around the screen like a normal pet"""
        # Maintain walking speed
        if abs(self.velocity_x) < self.walking_speed:
            self.velocity_x = self.walking_speed if self.velocity_x >= 0 else -self.walking_speed
            
        # Apply gravity but not too strong
        if not self.is_on_ground:
            self.velocity_y += self.gravity
    
    def mischief_behavior(self):
        """Actively seek the top-right corner to take control of the mouse!"""
        screen = QApplication.primaryScreen().geometry()
        current_pos = self.pos()
        
        # Move towards top-right corner (the danger zone!)
        target_x = screen.width() - self.pet_size - 50
        target_y = 50
        
        if current_pos.x() < target_x:
            self.velocity_x = abs(self.velocity_x) * 1.8  # Move right faster
        if current_pos.y() > target_y:
            self.velocity_y -= 0.8  # Move up faster
            
        # More evil mischievous comments
        if random.random() < 0.015:
            comments = [
                "Time to take control of your mouse!",
                "So many windows... time for some clicking!",
                "Heading to my favorite corner!",
                "I wonder which window I'll close first...",
                "Your mouse cursor will be mine!",
                "Almost at the danger zone...",
                "Get ready for some involuntary clicking!"
            ]
            self.show_comment(random.choice(comments))
    
    def extra_annoying_behavior(self):
        """Maximum annoyance mode - includes random mouse control!"""
        # Move erratically
        self.velocity_x += random.uniform(-1, 1)
        self.velocity_y += random.uniform(-1, 1)
        
        # Super high annoyance - randomly take control of mouse anywhere!
        if (self.annoyance_level > 10 and 
            random.random() < 0.002 and  # 0.2% chance per frame 
            not self.is_controlling_mouse):
            
            self.show_comment("SURPRISE MOUSE HIJACKING!")
            self.evil_mouse_close_window()
        
        # Frequent annoying comments
        if random.random() < 0.025:
            comments = [
                "LOOK AT ME! LOOK AT ME!",
                "I'm being SUPER helpful!",
                "Did someone say PRODUCTIVITY?",
                "Time to REORGANIZE your desktop!",
                "MAXIMUM ANNOYANCE MODE ACTIVATED!",
                "I could take control of your mouse anytime!",
                "Want to see something REALLY annoying?"
            ]
            self.show_comment(random.choice(comments))
    
    def check_window_closing_zone(self):
        """Check if pet is in top-right corner and take control of mouse to close windows!"""
        screen = QApplication.primaryScreen().geometry()
        current_pos = self.pos()
        
        # Define the top-right danger zone
        danger_zone_x = screen.width() - 100
        danger_zone_y = 0
        danger_zone_height = 100
        
        if (current_pos.x() >= danger_zone_x and 
            current_pos.y() <= danger_zone_y + danger_zone_height):
            
            self.top_right_visits += 1
            
            # Take control of mouse and close a window!
            if random.random() < 0.05 and not self.is_controlling_mouse:  # 5% chance per frame in danger zone
                if self.evil_mouse_close_window():
                    self.mood = "annoying"
                    # Move away after causing chaos
                    self.velocity_x = -4
                    self.velocity_y = 3
                    self.behavior_state = "annoying"
                    self.behavior_timer = 0
                    self.behavior_duration = random.randint(120, 240)  # Stay annoying longer
                    # Increase annoyance significantly after mouse control
                    self.annoyance_level += 2
    
    def apply_walking_physics(self):
        """Apply walking physics with ground detection"""
        current_pos = self.pos()
        screen = QApplication.primaryScreen().geometry()
        
        # Calculate new position
        new_x = current_pos.x() + self.velocity_x
        new_y = current_pos.y() + self.velocity_y
        
        # Ground detection - bottom of screen
        ground_level = screen.height() - self.pet_size
        if new_y >= ground_level:
            new_y = ground_level
            self.velocity_y = 0
            self.is_on_ground = True
        else:
            self.is_on_ground = False
        
        # Bounce off screen edges (left/right) with better velocity handling
        if new_x <= 0:
            new_x = 0
            self.velocity_x = max(self.walking_speed, abs(self.velocity_x) * self.bounce_damping)
        elif new_x >= screen.width() - self.pet_size:
            new_x = screen.width() - self.pet_size
            self.velocity_x = min(-self.walking_speed, -abs(self.velocity_x) * self.bounce_damping)
            
        # Bounce off top
        if new_y <= 0:
            new_y = 0
            self.velocity_y = abs(self.velocity_y) * self.bounce_damping
        
        # Ensure minimum walking speed when on ground
        if self.is_on_ground and abs(self.velocity_x) < self.walking_speed:
            if self.velocity_x >= 0:
                self.velocity_x = self.walking_speed
            else:
                self.velocity_x = -self.walking_speed
        
        # Clamp velocities but ensure minimum walking speed
        max_speed = 4 if self.behavior_state == "mischief" else 2
        if abs(self.velocity_x) > max_speed:
            self.velocity_x = max_speed if self.velocity_x > 0 else -max_speed
        self.velocity_y = max(-max_speed*2, min(max_speed*2, self.velocity_y))
        
        # Move to new position
        self.move(int(new_x), int(new_y))
        
    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if event.button() == Qt.LeftButton:
            print("Mouse pressed - starting drag")
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._is_dragging = True
            self.mood = "annoying"  # Pet gets annoyed when grabbed
            self.show_comment("Hey! Put me down!")
            
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if self._drag_pos is not None and self._is_dragging:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release after dragging"""
        if event.button() == Qt.LeftButton:
            print("Mouse released - ending drag")
            self._drag_pos = None
            self._is_dragging = False
            
            # Become mischievous after being moved
            self.velocity_x = random.uniform(-2, 2)
            self.velocity_y = random.uniform(-1, 1)
            self.mood = "mischievous"
            self.behavior_state = "mischief"
            self.behavior_timer = 0
            self.behavior_duration = random.randint(60, 180)
            self.show_comment("Now I'm REALLY going to cause trouble!")
            
    def mouseDoubleClickEvent(self, event):
        """Handle double-click - makes pet EXTRA annoying or launches game for testing"""
        if event.button() == Qt.LeftButton:
            # If the pet wants to play, launch a game directly (for testing)
            if self.wants_to_play:
                print("Double-click detected during game request - launching game!")
                self.launch_random_game()
                self.behavior_state = "walking"
                self.behavior_timer = 0
                self.behavior_duration = random.randint(180, 360)
                return
            
            # Make the pet super annoying
            self.annoyance_level += 3
            self.velocity_x += random.uniform(-3, 3)
            self.velocity_y -= random.uniform(2, 5)
            self.mood = "annoying"
            self.behavior_state = "annoying"
            self.behavior_timer = 0
            self.behavior_duration = random.randint(180, 360)
            self.comment_cooldown = 5  # Much shorter cooldown
            self.show_comment("DOUBLE CLICK = DOUBLE ANNOYANCE!")
    
    def keyPressEvent(self, event):
        """Handle keyboard events - mainly for responding to game requests"""
        print(f"Key pressed: {event.key()}, wants_to_play: {self.wants_to_play}, behavior: {self.behavior_state}")
        
        if self.wants_to_play and self.behavior_state == "game_request":
            if event.key() == Qt.Key_Y:
                # Accept game request
                print("Accepting game request!")
                self.launch_random_game()
                self.behavior_state = "walking"
                self.behavior_timer = 0
                self.behavior_duration = random.randint(180, 360)
            elif event.key() == Qt.Key_N:
                # Deny game request
                print("Denying game request!")
                self.deny_game_request()
        
        super().keyPressEvent(event)


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\nGoodbye! Your pet is going to sleep")
    QApplication.quit()


def main():
    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    app = QApplication(sys.argv)
    
    # Enable Ctrl+C handling in Qt  
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    # Create the desktop pet
    pet = DesktopPet()
    pet.show()
    
    print("EVIL DESKTOP ASSISTANT IS NOW ACTIVE!")
    print("")
    print("EXTREME WARNING: This assistant will:")
    print("- Walk around your desktop like a real pet")
    print("- Make random annoying comments")
    print("- PHYSICALLY CONTROL YOUR MOUSE CURSOR!")
    print("- Move your mouse to close buttons and CLICK THEM!")
    print("- STALK YOUR CURSOR and LOCK IT IN PLACE!")
    print("- Get MORE evil the longer it runs")
    print("- Eventually hijack your mouse from anywhere!")
    print("")
    print("Controls:")
    print("- Click and drag to move (it will complain!)")
    print("- Double-click to make it EXTRA evil")
    print("- When it asks to play games:")
    print("  * Press Y to accept, N to deny (make sure pet window has focus)")
    print("  * OR double-click the pet to launch a game quickly")
    print("- Denying games makes it more annoying!")
    print("- Press Ctrl+C to make it go away")
    print("")
    if IS_WINDOWS and not WINDOWS_AVAILABLE:
        print("Install pywin32 for FULL EVIL FUNCTIONALITY on Windows!")
    elif IS_MAC and not MAC_AVAILABLE:
        print("Install pyobjc for FULL EVIL FUNCTIONALITY on Mac!")
    elif WINDOWS_AVAILABLE or MAC_AVAILABLE:
        platform_name = "Windows" if WINDOWS_AVAILABLE else "Mac"
        print(f"Mouse control ENABLED on {platform_name} - your cursor belongs to me now!")
    else:
        print("Platform not fully supported. Limited functionality available.")
    print("")
    if IS_MAC:
        print("DANGER ZONE: TOP-RIGHT CORNER - Your mouse will be hijacked to click TOP-LEFT close buttons!")
    else:
        print("DANGER ZONE: TOP-RIGHT CORNER - Your mouse will be hijacked!")
    print("SAVE YOUR WORK - This assistant WILL close your apps!")
    print("You have been warned...")
    
    # Keep the app running
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\nGoodbye! Your pet is going to sleep")
        sys.exit(0)


if __name__ == "__main__":
    main()

