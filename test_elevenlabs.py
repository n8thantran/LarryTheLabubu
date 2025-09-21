#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for updated ElevenLabs voice functionality
"""

import os
import sys

# Load .env file first
try:
    from dotenv import load_dotenv
    load_dotenv()  # This loads the .env file
except ImportError:
    pass

def test_elevenlabs():
    print("Testing Updated ElevenLabs Voice System")
    print("=" * 50)

    # Check API key
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key or api_key == 'your_api_key_here':
        print("No ElevenLabs API key found!")
        print("Set your API key with:")
        print("export ELEVENLABS_API_KEY=your_actual_api_key_here")
        print("\nOr create a .env file with:")
        print("ELEVENLABS_API_KEY=your_actual_api_key_here")
        return False

    print(f"API key found: {api_key[:10]}...")

    # Test imports
    try:
        import pygame
        print("Pygame available")
    except ImportError:
        print("Pygame not available - install with: pip install pygame")
        return False

    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs import play
        print("ElevenLabs package (new SDK) available")
    except ImportError:
        print("ElevenLabs (new SDK) not available - install with: pip install elevenlabs")
        return False

    # Test dotenv (optional)
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("python-dotenv available (loading .env file)")
    except ImportError:
        print("python-dotenv not available (optional) - install with: pip install python-dotenv")

    # Test voice system
    try:
        from voice_system import LabubuVoice
        print("Voice system module loaded")

        # Initialize voice system
        voice = LabubuVoice()

        if voice.is_voice_available():
            print("Voice system initialized successfully!")
            print(f"Using voice ID: {voice.voice_id}")
            print(f"Using model: {voice.model_id}")
            print("Testing Labubu phrase...")

            # Test a Labubu phrase
            phrase = voice.speak_labubu_phrase()
            print(f"Speaking: '{phrase}'")

            # Wait a moment for the voice to finish
            import time
            print("Waiting for audio to complete...")
            time.sleep(4)

            print("Voice test completed!")
            return True
        else:
            print("Voice system not available")
            if not voice.client:
                print("   - ElevenLabs client not initialized")
            if not voice.voice_enabled:
                print("   - Voice not enabled")
            if not voice.audio_available:
                print("   - Audio system not available")
            return False

    except Exception as e:
        print(f"Error testing voice system: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting ElevenLabs voice test with updated SDK...")
    print()

    success = test_elevenlabs()

    print()
    if success:
        print("Voice system is ready!")
        print("Run 'python desktop_pet.py' to start Labubu with voice!")
        print("Labubu will randomly speak: 'labu-labu', 'labuubuulabuubuu', 'six seven', 'forty-one'")
        print("Press 'L' key while pet has focus to trigger manual voice")
    else:
        print("Voice system needs setup. Check the errors above.")
        print("See VOICE_SETUP.md for detailed instructions.")
        print("Make sure you have:")
        print("   1. Valid ELEVENLABS_API_KEY set as environment variable")
        print("   2. ElevenLabs credits available")
        print("   3. Internet connection")

    sys.exit(0 if success else 1)