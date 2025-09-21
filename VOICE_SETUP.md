# 🎤 Labubu Voice Setup

Your Labubu desktop pet has voice capabilities using ElevenLabs! Here's how to set it up:

## Quick Setup (2 minutes)

### 1. Get ElevenLabs API Key
1. Go to [https://elevenlabs.io](https://elevenlabs.io)
2. Sign up for a free account (10,000 characters/month free)
3. Go to your profile page
4. Copy your API key

### 2. Set the API Key
Choose one method:

**Option A: Temporary (current session only)**
```bash
export ELEVENLABS_API_KEY=your_actual_api_key_here
```

**Option B: Permanent (add to your shell profile)**
```bash
echo 'export ELEVENLABS_API_KEY=your_actual_api_key_here' >> ~/.zshrc
source ~/.zshrc
```

### 3. Test the Setup
```bash
source venv/bin/activate
python test_elevenlabs.py
```

### 4. Run Labubu with Voice
```bash
source venv/bin/activate
python desktop_pet.py
```

## Labubu's Voice Features

### 🗣️ Signature Phrases
Labubu will randomly speak:
- **"labu-labu"** - Classic Labubu greeting
- **"labuubuulabuubuu"** - Labubu's signature song
- **"six seven"** - Mysterious Labubu phrase  
- **"forty-one"** - Another Labubu classic

### ⏰ Voice Timing
- **Automatic**: Every 5-10 seconds during normal behavior
- **Manual**: Press **L** key while pet has focus
- **Game requests**: Sings "labuubuulabuubuu" when asking to play

### 🎮 Controls
- **L key** - Make Labubu speak immediately
- **Automatic** - Labubu speaks during normal behavior
- **Integrated** - Voice works with all existing behaviors

## Troubleshooting

**No voice?**
- Check that your API key is set: `echo $ELEVENLABS_API_KEY`
- Make sure you have credits on ElevenLabs (free tier: 10,000 characters/month)
- Check system audio is working

**ElevenLabs errors?**
- Verify API key is correct
- Check your internet connection
- Make sure you have available credits

**Labubu works without voice?**
- Yes! All visual features work normally
- Text comments still appear in console
- Just no audio speech

## Example Setup

```bash
# 1. Set API key
export ELEVENLABS_API_KEY=sk_1234567890abcdef...

# 2. Install dependencies (if not already installed)
pip install elevenlabs pygame python-dotenv

# 3. Test voice (new updated test)
python test_elevenlabs.py

# 4. Run Labubu
python desktop_pet.py
```

## Optional: Custom Voice & Model Settings

You can customize Labubu's voice by setting these environment variables:

```bash
# Optional: Custom voice ID (default is Bella)
export ELEVENLABS_VOICE_ID=your_voice_id_here

# Optional: Custom model (default is eleven_multilingual_v2)
export ELEVENLABS_MODEL_ID=eleven_monolingual_v1
```

Or add them to a `.env` file in the project directory:
```
ELEVENLABS_API_KEY=your_api_key_here
ELEVENLABS_VOICE_ID=your_voice_id_here
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
```

Enjoy your talking Labubu! 🎤✨
