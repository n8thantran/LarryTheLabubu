#!/usr/bin/env python3
"""
Voice system for Labubu using ElevenLabs
"""

import os
import threading
import time
import pygame
import tempfile

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file if it exists
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

# Try to import ElevenLabs
try:
    from elevenlabs import generate, save, set_api_key, Voice, VoiceSettings
    ELEVENLABS_AVAILABLE = True
except ImportError:
    print("ElevenLabs not available - voice features disabled")
    ELEVENLABS_AVAILABLE = False

class LabubuVoice:
    def __init__(self, api_key=None):
        """Initialize the Labubu voice system"""
        self.api_key = api_key or os.getenv('ELEVENLABS_API_KEY')
        self.voice_enabled = False
        self.voice_queue = []
        self.is_speaking = False
        
        # Initialize pygame mixer for audio playback
        try:
            pygame.mixer.init()
            self.audio_available = True
        except:
            print("Pygame mixer not available - voice disabled")
            self.audio_available = False
        
        # Set up ElevenLabs if API key is available and ElevenLabs is installed
        if ELEVENLABS_AVAILABLE and self.api_key and self.audio_available:
            try:
                set_api_key(self.api_key)
                self.voice_enabled = True
                print("Labubu voice system initialized! 🎤")
                
                # Get voice ID from .env file if available
                voice_id = os.getenv('ELEVENLABS_VOICE_ID', 'EXAVITQu4vr4xnSDxMaL')  # Default to Bella
                
                # Voice settings for Labubu (cute, playful voice)
                self.voice_settings = VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.8,
                    style=0.3,
                    use_speaker_boost=True
                )
                
                # Use the voice ID from .env or default
                self.voice = Voice(
                    voice_id=voice_id,
                    settings=self.voice_settings
                )
                
                print(f"Using voice ID: {voice_id}")
                
            except Exception as e:
                print(f"Failed to initialize ElevenLabs: {e}")
                self.voice_enabled = False
        else:
            if not ELEVENLABS_AVAILABLE:
                print("ElevenLabs package not available - voice disabled")
            elif not self.api_key or self.api_key == 'your_api_key_here':
                print("No ElevenLabs API key found. Set ELEVENLABS_API_KEY environment variable.")
            self.voice_enabled = False
        
        # Labubu's special phrases
        self.labubu_phrases = [
            "labu-labu",
            "labuubuulabuubuu", 
            "six seven",
            "forty-one"
        ]
        
        # Voice settings will be set above if ElevenLabs is available and API key is valid
        if not self.voice_enabled:
            self.voice_settings = None
            self.voice = None
        
    def set_api_key(self, api_key):
        """Set ElevenLabs API key"""
        if not ELEVENLABS_AVAILABLE:
            print("ElevenLabs not available")
            return
            
        self.api_key = api_key
        try:
            set_api_key(self.api_key)
            self.voice_enabled = True
            print("ElevenLabs API key set successfully!")
        except Exception as e:
            print(f"Failed to set API key: {e}")
            self.voice_enabled = False
    
    def speak_async(self, text, priority=False):
        """Add text to voice queue for asynchronous playback"""
        if not self.voice_enabled or not self.audio_available:
            return
        
        # If it's a Labubu special phrase, use it directly
        if text.lower() in [phrase.lower() for phrase in self.labubu_phrases]:
            text = text.lower()
        
        if priority:
            self.voice_queue.insert(0, text)
        else:
            self.voice_queue.append(text)
        
        # Start voice thread if not already running
        if not self.is_speaking:
            voice_thread = threading.Thread(target=self._voice_worker, daemon=True)
            voice_thread.start()
    
    def speak_immediate(self, text):
        """Speak text immediately (blocking)"""
        if not ELEVENLABS_AVAILABLE or not self.voice_enabled or not self.audio_available:
            return
        
        try:
            # Generate speech
            audio = generate(
                text=text,
                voice=self.voice,
                model="eleven_monolingual_v1"
            )
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                save(audio, temp_file.name)
                
                # Play audio
                self._play_audio_file(temp_file.name)
                
                # Clean up
                os.unlink(temp_file.name)
                
        except Exception as e:
            print(f"Voice generation failed: {e}")
    
    def _voice_worker(self):
        """Background worker for voice queue"""
        self.is_speaking = True
        
        while self.voice_queue and self.voice_enabled and ELEVENLABS_AVAILABLE:
            text = self.voice_queue.pop(0)
            
            try:
                # Generate speech
                audio = generate(
                    text=text,
                    voice=self.voice,
                    model="eleven_monolingual_v1"
                )
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                    save(audio, temp_file.name)
                    
                    # Play audio
                    self._play_audio_file(temp_file.name)
                    
                    # Clean up
                    os.unlink(temp_file.name)
                    
            except Exception as e:
                print(f"Voice generation failed for '{text}': {e}")
        
        self.is_speaking = False
    
    def _play_audio_file(self, file_path):
        """Play audio file using pygame"""
        try:
            # Load and play audio
            sound = pygame.mixer.Sound(file_path)
            sound.play()
            
            # Wait for playback to finish
            while pygame.mixer.get_busy():
                time.sleep(0.1)
                
        except Exception as e:
            print(f"Audio playback failed: {e}")
    
    def speak_labubu_phrase(self):
        """Speak a random Labubu phrase"""
        import random
        phrase = random.choice(self.labubu_phrases)
        self.speak_async(phrase, priority=True)
        return phrase
    
    def is_voice_available(self):
        """Check if voice system is available"""
        return self.voice_enabled and self.audio_available
    
    def clear_queue(self):
        """Clear the voice queue"""
        self.voice_queue.clear()
