# Hand Alternator Game - CV Setup Guide

The Hand Alternator game is a computer vision-based game that tracks your hand movements using your webcam.

## Requirements

### Software Dependencies
**Basic Requirements (Required):**
```bash
pip install opencv-python numpy
```

**Advanced Hand Tracking (Optional):**
```bash
pip install mediapipe
```

### Hardware Requirements
- A working webcam/camera connected to your computer
- Good lighting (helps with detection)
- Clear background (recommended)

## Game Modes

### 1. **Advanced Mode** (with MediaPipe)
- Precise hand landmark tracking
- Detects exact hand positions
- More accurate gameplay

### 2. **Motion Detection Mode** (OpenCV only)
- Uses motion detection in screen regions
- Move hands in LEFT and RIGHT areas of the screen
- Less precise but still functional

### 3. **Simulation Mode** (no camera)
- Click "Simulate Success" to test
- Use "🔄 Retry Camera" if camera becomes available

## Game Instructions

1. **Start the Game**: The pet will randomly request the Hand Alternator game, or you can trigger it manually with I/O/G keys.

2. **Camera Setup**: The game will automatically detect and test your camera.

3. **Hand Positions**: 
   - **Advanced Mode**: Show both hands, alternate which is higher
   - **Motion Mode**: Wave hands in LEFT and RIGHT screen regions
   - Hold each position for 1 second

4. **Win Condition**: Complete 10 alternations within 30 seconds to win!

5. **Camera Issues**: Click "🔄 Retry Camera" if camera becomes available during gameplay.

## Troubleshooting

### Camera Issues
- Make sure your webcam is not being used by another application
- Check that your camera drivers are up to date
- Try restarting the game if camera access fails

### Dependency Issues
If you get import errors, install the dependencies:
```bash
pip install opencv-python mediapipe numpy
```

### Performance Issues
- Close other applications that might be using the camera
- Ensure good lighting for better hand detection
- Try different hand positions if detection is poor

## Game Integration

The Hand Alternator is fully integrated with the pet's punishment/reward system:
- **Winning** calms the pet and reduces annoyance
- **Losing** triggers punishment mode with escalating chaos
- The pet **never closes** regardless of game outcomes
- Failed games lead to immediate window closing and cursor hijacking

Have fun with the CV-powered Hand Alternator game! 🎮📷

