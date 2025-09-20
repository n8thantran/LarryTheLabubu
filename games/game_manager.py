"""Game manager to handle game selection and launching for the desktop pet"""

import random
import importlib
import os
from typing import List, Type, Optional
from .base_game import BaseGame


class GameManager:
    """Manages available games and handles game selection/launching"""
    
    def __init__(self):
        self.available_games = []
        self.current_game = None
        self.game_request_cooldown = 0
        self.last_game_time = 0
        self.game_result_callback = None  # Callback for game results
        self._discover_games()
        
    def _discover_games(self):
        """Automatically discover all available games in the games package"""
        games_dir = os.path.dirname(__file__)
        
        for filename in os.listdir(games_dir):
            if filename.endswith('.py') and not filename.startswith('_') and filename != 'base_game.py' and filename != 'game_manager.py':
                module_name = filename[:-3]  # Remove .py extension
                try:
                    # Import the module
                    module = importlib.import_module(f'games.{module_name}')
                    
                    # Look for classes that inherit from BaseGame
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            issubclass(attr, BaseGame) and 
                            attr != BaseGame):
                            self.available_games.append(attr)
                            print(f"Discovered game: {attr_name}")
                except Exception as e:
                    print(f"Failed to import game module {module_name}: {e}")
    
    def get_random_game(self) -> Optional[Type[BaseGame]]:
        """Get a random game class from available games"""
        if not self.available_games:
            return None
        return random.choice(self.available_games)
    
    def launch_game(self, game_class: Optional[Type[BaseGame]] = None) -> Optional[BaseGame]:
        """Launch a game (random if none specified)"""
        if game_class is None:
            game_class = self.get_random_game()
        
        if game_class is None:
            print("No games available to launch!")
            return None
        
        try:
            # Close current game if one is running
            if self.current_game:
                self.current_game.end_game()
                self.current_game.close()
            
            # Create and start new game
            self.current_game = game_class()
            self.current_game.set_result_callback(self.game_result_callback)
            self.current_game.start_game()
            self.current_game.show()
            print(f"Launched game: {self.current_game.game_name}")
            return self.current_game
            
        except Exception as e:
            print(f"Failed to launch game: {e}")
            return None
    
    def is_game_running(self) -> bool:
        """Check if a game is currently running"""
        return self.current_game is not None and self.current_game.game_active
    
    def close_current_game(self):
        """Close the currently running game"""
        if self.current_game:
            self.current_game.end_game()
            self.current_game.close()
            self.current_game = None
    
    def close_current_game_safely(self):
        """Safely close the currently running game without affecting the pet"""
        if self.current_game:
            print(f"🎮 Safely closing game: {self.current_game.game_name}")
            
            # End the game logic first
            self.current_game.end_game()
            
            # Hide the window instead of closing it completely
            self.current_game.hide()
            
            # Clean up the reference
            self.current_game = None
            
            print("✅ Game closed successfully, pet continues running!")
    
    def get_available_games_info(self) -> List[dict]:
        """Get information about all available games"""
        games_info = []
        for game_class in self.available_games:
            try:
                # Create temporary instance to get info
                temp_game = game_class()
                games_info.append(temp_game.get_game_info())
                temp_game.deleteLater()
            except Exception as e:
                print(f"Error getting info for game {game_class.__name__}: {e}")
        return games_info
    
    def set_game_result_callback(self, callback):
        """Set the callback function for when games end"""
        self.game_result_callback = callback
    
    def update(self):
        """Update the game manager (call this regularly)"""
        self.game_request_cooldown = max(0, self.game_request_cooldown - 1)
        
        # Check if current game is finished
        if self.current_game and not self.current_game.game_active:
            if self.current_game.is_game_finished():
                print(f"Game {self.current_game.game_name} finished!")
                self.close_current_game_safely()
    
    def should_request_game(self) -> bool:
        """Determine if the pet should request to play a game"""
        # Don't request if already playing or on cooldown
        if self.is_game_running() or self.game_request_cooldown > 0:
            return False
        
        # Random chance to want to play
        return random.random() < 0.001  # 0.1% chance per frame
    
    def deny_game_request(self):
        """Called when a game request is denied - sets cooldown"""
        self.game_request_cooldown = 300  # 5 seconds at 60fps


