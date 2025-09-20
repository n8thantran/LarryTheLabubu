#!/usr/bin/env python3
"""
Simple runner script for the Hand Alternator CV application
"""

from hand_alternator import HandAlternator

if __name__ == "__main__":
    print("Starting Hand Alternator...")
    print("Make sure your camera is connected and working.")
    print()
    
    try:
        app = HandAlternator()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication stopped by user.")
    except Exception as e:
        print(f"Error running application: {e}")
        print("Make sure your camera is working and try again.")


