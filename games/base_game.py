"""Base game class that all games should inherit from"""

from abc import ABC, abstractmethod
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QObject


class BaseGameMeta(type(QWidget), type(ABC)):
    """Metaclass to resolve conflict between QWidget and ABC"""
    pass


class BaseGame(QWidget, ABC, metaclass=BaseGameMeta):
    """Abstract base class for all games in the desktop pet system"""
    
    def __init__(self):
        super().__init__()
        self.game_active = False
        self.game_won = False
        self.game_lost = False
        self.game_name = "Unknown Game"
        self.game_description = "A mysterious game"
        self.play_duration = 30  # Default play duration in seconds
        
    @abstractmethod
    def start_game(self):
        """Start the game - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def end_game(self):
        """End the game - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def is_game_finished(self):
        """Check if the game is finished - must be implemented by subclasses"""
        pass
    
    def get_game_info(self):
        """Get basic information about this game"""
        return {
            'name': self.game_name,
            'description': self.game_description,
            'duration': self.play_duration
        }
    
    def reset_game(self):
        """Reset game state for a new play session"""
        self.game_active = False
        self.game_won = False
        self.game_lost = False
