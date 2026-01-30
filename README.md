# Roblox Auto Fisher

An automated bot for Roblox fishing minigames that uses computer vision to detect and control the fishing slider. The bot automatically tracks the white bobber and adjusts the slider position to keep it within the acceptable range.

## Features

- **Automatic Minigame Detection**: Detects when a fishing minigame appears on screen
- **Real-Time Tracking**: Uses OpenCV to track the white bobber and orange slider bar
- **Intelligent Control**: Automatically holds and releases the mouse button to keep the bobber in the target zone
- **Debug Mode**: Optional visual overlay to see what the bot is detecting
- **Safety Features**: Fail-safe by moving mouse to (0,0), automatic detection of stuck tracking
- **Hotkey Controls**: Easy toggle and emergency stop controls

## Requirements

- Python 3.7+
- Windows (uses `pyautogui` and `keyboard` modules)
- Roblox game running

### Dependencies

```
opencv-python>=4.8.0
pyautogui>=0.9.54
keyboard>=0.13.5
numpy>=1.24.0
Pillow>=10.0.0
```

## Installation

1. **Install Python**: Make sure you have Python 3.7 or later installed

2. **Clone or download this repository** to your desired location

3. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

## Usage

### Starting the Bot

1. Open Roblox and position yourself in an area where fishing minigames occur
2. Run the script:
   ```powershell
   python screen_tracker.py
   ```
3. The script will start and wait for commands (2-second startup delay)

### Controls

| Key | Action |
|-----|--------|
| **F6** | Toggle bot ON/OFF |
| **F8** | Quit the program |
| **Mouse to (0,0)** | Emergency stop (move your mouse to top-left corner) |

### How It Works

1. **Detection**: The bot continuously scans for the fishing minigame by looking for dark rectangular areas (the slider background) and orange bars
2. **Auto-Start** (optional): If enabled, the bot automatically activates when a minigame is detected
3. **Tracking**: Once the minigame is detected, the bot:
   - make sure your camera is facing down looking at the ground and have the side that the slider for when you catch a fish appears have the mouse on that side of the monitor
   - Locates the white bobber (fishing float)
   - Finds the orange slider bar
   - Calculates the difference between their positions
5. **Control**: 
   - If bobber is **below** the bar → **HOLD** the mouse button (pulls slider down)
   - If bobber is **above** the bar → **RELEASE** the mouse button (lets slider rise)
6. **Completion**: When the minigame ends, waits 6 seconds and clicks once

## Configuration

Edit `screen_tracker.py` to adjust these settings at the top of the file:

```python
# Auto-start when minigame appears (don't need to press F6/click)
AUTO_START_ON_DETECT = True

# Enable debug messages and visual overlay
DEBUG = False
DEBUG_OVERLAY = True

# Maximum width for minigame detection region (pixels)
REGION_MAX_WIDTH = 160

# How long to wait before considering mouse "frozen"
MOVEMENT_TIMEOUT = 1.0

# Minimum pixels mouse must move to be considered "active"
MIN_MOVEMENT_THRESHOLD = 2

# Control thresholds - adjust for faster/slower response
HOLD_THRESHOLD = 5       # How far below bar before holding
RELEASE_THRESHOLD = 2    # How far above bar before releasing

# Click to focus game before synthetic input
FIRST_FOCUS_CLICK = True
```

## Debug Mode

To see what the bot is detecting in real-time:

1. Set `DEBUG = True` in the script
2. Set `DEBUG_OVERLAY = True` to see visual overlay
3. Run the script
4. A window will appear showing:
   - White circle: Detected bobber position
   - Green circle: Last known bobber position
   - Blue vertical line: Slider center
   - Orange horizontal line: Orange bar position
   - Status text: Current state (held/released, difference value)

## Troubleshooting

### Bot not detecting minigame
- Check that the fishing area is visible and not covered by UI elements
- Increase `REGION_MAX_WIDTH` if the minigame region is being cut off
- Enable `DEBUG_OVERLAY` to see what the camera is capturing

### Bot moving mouse but not catching fish
- Adjust `HOLD_THRESHOLD` and `RELEASE_THRESHOLD` values
  - Lower values = more sensitive, faster response
  - Higher values = less sensitive, slower response
- Ensure `FIRST_FOCUS_CLICK = True` so the game window gets focus

### Mouse tracking gets "frozen"
- The bot has built-in detection for stuck tracking
- If detected, it automatically releases the mouse and resets
- Adjust `MOVEMENT_TIMEOUT` if needed

### Bot stops after one fish
- Make sure `AUTO_START_ON_DETECT = True` so it automatically restarts
- Or manually press F6 to toggle the bot back on between fish

## Files

- `screen_tracker.py` - Main bot script
- `create_template.py` - Utility to generate template images (for development)
- `requirements.txt` - Python package dependencies
- `assets/` - Folder for template images and other assets(not used)

## How The Bot Controls The Slider

The bot uses **hysteresis thresholds** to avoid rapid toggling:

```
Bobber Position vs Orange Bar:
↓ Below Bar → HOLD mouse (pulls slider down to bring bobber up)
→ Near Bar → Hysteresis zone (no change)
↑ Above Bar → RELEASE mouse (lets slider rise, bobber falls)
```

The thresholds prevent jittering and make the response more stable.

## Safety Features

- **Fail-safe**: Moving your mouse to the top-left corner (0,0) will immediately stop the bot
- **Stuck Detection**: If mouse hasn't moved in 1+ seconds, bot automatically resets and releases
- **Emergency Key**: Press F8 to completely quit the program
- **Auto-Release**: Mouse button is always released when minigame ends or bot is toggled off



## Disclaimer

This bot is for personal use and learning purposes. Use responsibly and follow the game's terms of service. The author is not responsible for any account suspensions or bans.

## License

Free to use and modify for personal purposes.
