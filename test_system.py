#!/usr/bin/env python3
"""Test script for the modular game system"""

import sys
from PySide6.QtWidgets import QApplication
from desktop_pet import DesktopPet

def main():
    print("Testing the modular desktop pet game system...")
    
    app = QApplication(sys.argv)
    
    # Create the desktop pet (which now includes game system)
    pet = DesktopPet()
    
    print(f"Available games: {len(pet.game_manager.available_games)}")
    for game_class in pet.game_manager.available_games:
        temp_game = game_class()
        info = temp_game.get_game_info()
        print(f"- {info['name']}: {info['description']}")
        temp_game.deleteLater()
    
    pet.show()
    
    print("\nPet is now running with integrated game system!")
    print("It will randomly request games, and if denied, become more annoying.")
    
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\nTest completed!")
        sys.exit(0)

if __name__ == "__main__":
    main()


