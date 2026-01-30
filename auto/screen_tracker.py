import pyautogui
import cv2
import numpy as np
import time
import os
from PIL import ImageGrab
import keyboard

# (OCR removed) - no pytesseract configuration

# Fail-safe: Moving mouse to (0,0) will stop the script
pyautogui.FAILSAFE = True

# Global control variables
is_bot_enabled = False
is_running = True
# Debug flag to print diagnostics
DEBUG = False
# Auto-start when minigame appears (so you don't have to press F6/click)
AUTO_START_ON_DETECT = True
# When DEBUG is enabled, show an on-screen OpenCV overlay with detection info
DEBUG_OVERLAY = True
# Maximum width (in pixels) for the detected minigame region to avoid capturing nearby UI bars
REGION_MAX_WIDTH = 160
# How long (seconds) to wait before considering mouse "frozen" if not moving
MOVEMENT_TIMEOUT = 1.0
# How many pixels the mouse must move to be considered "active"
MIN_MOVEMENT_THRESHOLD = 2
# Control thresholds (hysteresis) to avoid rapid toggling
HOLD_THRESHOLD = 5      # diff above this => hold mouse (reduced for faster response)
RELEASE_THRESHOLD = 2    # diff below this => release mouse (reduced for faster response)
# If Roblox requires a real click/focus before synthetic input works, enable this
FIRST_FOCUS_CLICK = True

def capture_screen():
    """Capture the entire screen"""
    screenshot = pyautogui.screenshot()
    return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

 

def detect_minigame(frame):
    """Detect if the fishing minigame is visible by finding the backpack icon"""
    # Revert to dark-bar + orange-bar detection (no template/OCR)
    # Convert to grayscale and threshold dark areas
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, mask_dark = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 15))
    mask_dark = cv2.morphologyEx(mask_dark, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask_dark, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = cv2.contourArea(contour)
        # Look for tall dark rectangles likely to be the slider box
        if h > 120 and h / (w + 1) > 3 and area > 1500:
            candidates.append((contour, x, y, w, h, area))

    if candidates:
        # Prefer largest area and leftmost if tie
        candidates.sort(key=lambda t: (-t[5], t[1]))
        _, x, y, w, h, _ = candidates[0]
        pad_left = 20
        pad_top = 40
        pad_right = 40
        pad_bottom = 80
        region_x = max(0, x - pad_left)
        region_y = max(0, y - pad_top)
        region_w = w + pad_left + pad_right
        region_h = h + pad_top + pad_bottom
        # Compute slider center relative to region
        slider_center_rel_x = (x + w // 2) - region_x

        # Limit horizontal size to avoid capturing nearby UI bars
        try:
            screen_w, _ = pyautogui.size()
        except Exception:
            screen_w = None

        slider_center_screen_x = x + w // 2
        if REGION_MAX_WIDTH is not None and region_w > REGION_MAX_WIDTH:
            new_region_w = int(REGION_MAX_WIDTH)
            new_region_x = int(slider_center_screen_x - new_region_w // 2)
            if new_region_x < 0:
                new_region_x = 0
            if screen_w is not None and (new_region_x + new_region_w) > screen_w:
                new_region_x = max(0, screen_w - new_region_w)
            # Recompute relative slider center
            slider_center_rel_x = slider_center_screen_x - new_region_x
            region_x = new_region_x
            region_w = new_region_w

        return (region_x, region_y, region_w, region_h, slider_center_rel_x)

    # Fallback: detect orange bar (older method) if dark bar detection fails
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_orange = np.array([15, 150, 150])
    upper_orange = np.array([30, 255, 255])
    mask = cv2.inRange(hsv, lower_orange, upper_orange)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        if cv2.contourArea(contour) > 500:
            x, y, w, h = cv2.boundingRect(contour)
            pad_left = 20
            pad_top = 50
            pad_right = 40
            pad_bottom = 100
            region_x = x - pad_left
            region_y = y - pad_top
            region_w = w + pad_left + pad_right
            region_h = h + pad_top + pad_bottom
            slider_center_rel_x = (x + w // 2) - region_x

            # Limit horizontal size to avoid capturing nearby UI bars
            try:
                screen_w, _ = pyautogui.size()
            except Exception:
                screen_w = None

            slider_center_screen_x = x + w // 2
            if REGION_MAX_WIDTH is not None and region_w > REGION_MAX_WIDTH:
                new_region_w = int(REGION_MAX_WIDTH)
                new_region_x = int(slider_center_screen_x - new_region_w // 2)
                if new_region_x < 0:
                    new_region_x = 0
                if screen_w is not None and (new_region_x + new_region_w) > screen_w:
                    new_region_x = max(0, screen_w - new_region_w)
                # Recompute relative slider center
                slider_center_rel_x = slider_center_screen_x - new_region_x
                region_x = new_region_x
                region_w = new_region_w

            return (region_x, region_y, region_w, region_h, slider_center_rel_x)

    return None

def capture_region(x, y, width, height):
    """Capture a specific region of the screen"""
    screenshot = pyautogui.screenshot(region=(x, y, width, height))
    return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

def find_orange_bar(frame):
    """Find the orange bar in the frame (Roblox specific)"""
    # Convert to HSV color space
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Define color range for Roblox's orange bar
    lower_orange = np.array([15, 150, 150])  # Brighter orange for Roblox
    upper_orange = np.array([30, 255, 255])
    
    # Create a mask for orange
    mask = cv2.inRange(hsv, lower_orange, upper_orange)
    
    # Apply some morphology to clean up the mask
    kernel = np.ones((3,3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        # Get the largest contour (should be the orange bar)
        largest_contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest_contour) > 100:  # Minimum size threshold
            # Get the vertical center of the bar
            y, _, h = cv2.boundingRect(largest_contour)[1:4]
            return y + h // 2
    return None

def find_white_ball(frame, expected_x=None, proximity_radius=80, edge_margin=3, min_area=20, max_area=5000):
    """Find the white ball in the frame (Roblox specific).

    If expected_x is provided (region-relative), prefer contours whose center x
    is closest to expected_x. This helps avoid picking white UI elements far from
    the slider when the bobber is above the bar.
    """
    # Convert to HSV color space
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Define color range for Roblox's white ball
    lower_white = np.array([0, 0, 220])  # Pure white with high brightness
    upper_white = np.array([180, 20, 255])
    
    # Create a mask for white
    mask = cv2.inRange(hsv, lower_white, upper_white)
    
    # Apply morphology to clean up the mask
    kernel = np.ones((2,2), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Fallback to contour detection
    if not contours:
        return None

    h, w = frame.shape[:2]

    # Filter contours by area to avoid noise and optionally ignore those touching the frame edges
    valid_centers = []
    for c in contours:
        area = cv2.contourArea(c)
        if not (min_area < area < max_area):
            continue
        bx, by, bw, bh = cv2.boundingRect(c)

        # Ignore contours that touch or are very near the region border (likely the white frame)
        if edge_margin is not None and (bx <= edge_margin or by <= edge_margin or (bx + bw) >= (w - edge_margin) or (by + bh) >= (h - edge_margin)):
            continue

        cx = bx + bw // 2
        cy = by + bh // 2
        valid_centers.append((cx, cy, area))

    if not valid_centers:
        return None

    # If expected_x is provided, prefer contours close to that x (slider center).
    if expected_x is not None:
        close = [t for t in valid_centers if abs(t[0] - expected_x) <= proximity_radius]
        if close:
            close.sort(key=lambda t: abs(t[0] - expected_x))
            chosen = close[0]
            return (chosen[0], chosen[1])

        # Fallback: if none are within the radius, pick the contour whose x is closest
        valid_centers.sort(key=lambda t: abs(t[0] - expected_x))
        chosen = valid_centers[0]
        return (chosen[0], chosen[1])

    # No expected_x: pick the largest valid contour
    valid_centers.sort(key=lambda t: t[2], reverse=True)
    chosen = valid_centers[0]
    return (chosen[0], chosen[1])

def toggle_bot(e):
    """Toggle the bot on/off"""
    global is_bot_enabled
    is_bot_enabled = not is_bot_enabled
    print(f"Bot {'enabled' if is_bot_enabled else 'disabled'}")

def stop_program(e):
    """Stop the program completely"""
    global is_running
    is_running = False
    print("Stopping the program...")
    pyautogui.mouseUp()  # Make sure to release mouse button

def main():
    global is_bot_enabled, is_running
    
    print("=== Roblox Auto Fisher ===")
    print("Controls:")
    print("- Press F6 to toggle bot ON/OFF")
    print("- Press F8 to quit the program")
    print("- Move mouse to (0,0) for emergency stop")
    print("\nWaiting for commands...")
    
    # Setup hotkeys
    keyboard.on_press_key('F6', toggle_bot)
    keyboard.on_press_key('F8', stop_program)
    
    # Define the acceptable range around the center (tolerance)
    tolerance = 10  # Tolerance for ball position relative to bar
    
    try:
        while is_running:
            # If bot is enabled (or auto-start is allowed), check for a minigame
            if is_bot_enabled or AUTO_START_ON_DETECT:
                full_screen = capture_screen()
                minigame_region = detect_minigame(full_screen)

                if minigame_region is not None:
                    # Minigame detected, get the region
                    x, y, width, height, slider_center_rel_x = minigame_region

                    # Auto-enable if configured
                    if AUTO_START_ON_DETECT and not is_bot_enabled:
                        is_bot_enabled = True
                        if DEBUG:
                            print("Auto-enabled bot because minigame detected")

                    # Enter a focused inner loop that runs while the minigame remains visible
                    mouse_held = False
                    # Optionally send one click to focus the game so synthetic input registers
                    focused_once = False
                    # Keep last known ball position to avoid brief losses
                    last_ball_rel = None
                    last_ball_time = 0
                    # Track mouse movement to detect if tracking gets stuck
                    last_mouse_pos = pyautogui.position()
                    last_mouse_move_time = time.time()
                    last_detection_reset = 0
                    while is_running and is_bot_enabled:
                        # Re-capture the full screen and check whether the minigame still exists
                        full_screen = capture_screen()
                        current_region = detect_minigame(full_screen)
                        if current_region is None:
                            # Minigame disappeared
                            break

                        # Unpack current region and slider center
                        x, y, width, height, slider_center_rel_x = current_region

                        # Capture and process the current minigame region
                        frame = capture_region(x, y, width, height)

                        # Find positions of the orange bar and white ball
                        bar_y = find_orange_bar(frame)
                        ball_pos = find_white_ball(frame, expected_x=slider_center_rel_x)

                        # If primary detection fails, try a wider/fallback search (larger proximity, allow edges)
                        if ball_pos is None:
                            if DEBUG:
                                print("Primary white-ball detection failed; trying expanded search")
                            ball_pos = find_white_ball(frame, expected_x=slider_center_rel_x, proximity_radius=200, edge_margin=0, min_area=10, max_area=15000)
                            if ball_pos is not None and DEBUG:
                                print("Fallback detection succeeded")

                        # If still none, but we recently saw the ball, reuse last known position briefly
                        if ball_pos is None and last_ball_rel is not None and (time.time() - last_ball_time) <= 0.5:
                            if DEBUG:
                                print("Using recent last-known ball position to avoid transient loss")
                            ball_x, ball_y = last_ball_rel
                            # Do not update last_ball_time here
                        elif ball_pos is not None:
                            ball_x, ball_y = ball_pos
                            # Update last-known relative ball position and timestamp
                            last_ball_rel = (ball_x, ball_y)
                            last_ball_time = time.time()

                            # Move cursor to the bobber (do this regardless of bar detection)
                            screen_x = x + ball_x
                            screen_y = y + ball_y
                            diff = None  # Initialize diff here so it's always defined
                            try:
                                # Move mouse instantly for maximum speed
                                pyautogui.moveTo(screen_x, screen_y, duration=0)
                                # Minimal settle time
                                time.sleep(0.005)
                            except Exception as e:
                                if DEBUG:
                                    print(f"Mouse move error: {e}")

                            # Optionally focus the game window with a real click once
                            if FIRST_FOCUS_CLICK and not focused_once:
                                try:
                                    pyautogui.click(x + width // 2, y + height // 2)
                                except Exception:
                                    pass
                                focused_once = True
                                # small pause after focus click
                                time.sleep(0.05)

                            # Decide whether to hold or release using hysteresis thresholds
                            # Only make hold/release decisions if we detected the orange bar
                            if bar_y is not None:
                                diff = ball_y - bar_y
                                # Negative diff means bobber is below the bar (need to hold to pull slider down)
                                # Positive diff means bobber is above the bar (need to release to let slider rise)
                                if diff < -HOLD_THRESHOLD:  # Bobber is below bar by more than threshold
                                    if not mouse_held:
                                        try:
                                            pyautogui.mouseDown(button='left')
                                            mouse_held = True
                                            if DEBUG:
                                                print(f"HOLD (bobber below) - diff={diff}, screen=({screen_x},{screen_y})")
                                        except Exception as e:
                                            if DEBUG:
                                                print(f"Mouse down error: {e}")
                                elif diff > -RELEASE_THRESHOLD:  # Bobber is at or above bar
                                    if mouse_held:
                                        try:
                                            pyautogui.mouseUp(button='left')
                                            mouse_held = False
                                            if DEBUG:
                                                print(f"RELEASE (bobber above) - diff={diff}, screen=({screen_x},{screen_y})")
                                        except Exception as e:
                                            if DEBUG:
                                                print(f"Mouse up error: {e}")
                            else:
                                # If we don't see the orange bar, be conservative and release
                                diff = None
                                if mouse_held:
                                    try:
                                        pyautogui.mouseUp(button='left')
                                        mouse_held = False
                                        if DEBUG:
                                            print("RELEASE - no orange bar detected")
                                    except Exception as e:
                                        if DEBUG:
                                            print(f"Mouse up error: {e}")
                        else:
                            # If we can't see ball or bar, release to be safe
                            if mouse_held:
                                pyautogui.mouseUp(button='left')
                                mouse_held = False
                                if DEBUG:
                                    print("RELEASE - lost detection")

                        # Draw debug overlay in the region if requested
                        try:
                            if DEBUG and DEBUG_OVERLAY:
                                viz = frame.copy()
                                # Draw slider center vertical line
                                scx = int(slider_center_rel_x)
                                cv2.line(viz, (scx, 0), (scx, height), (200, 200, 0), 1)

                                # Draw orange bar center
                                if bar_y is not None:
                                    cv2.line(viz, (0, int(bar_y)), (width, int(bar_y)), (0, 165, 255), 2)

                                # Draw detected ball
                                if 'ball_x' in locals() and 'ball_y' in locals():
                                    cv2.circle(viz, (int(ball_x), int(ball_y)), 6, (255, 255, 255), -1)

                                # Draw last known ball position if present
                                if 'last_ball_rel' in locals() and last_ball_rel is not None:
                                    lx, ly = last_ball_rel
                                    cv2.circle(viz, (int(lx), int(ly)), 4, (0, 255, 0), 2)

                                # Show hold state and diff
                                status_text = f"held={mouse_held} diff={diff if 'diff' in locals() else 'N/A'}"
                                cv2.putText(viz, status_text, (8, height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

                                # Show the overlay window
                                cv2.imshow('Fisher Debug', viz)
                                cv2.waitKey(1)
                        except Exception as e:
                            if DEBUG:
                                print(f"Debug overlay error: {e}")

                        # Break out if bot was toggled off while inside
                        if not is_bot_enabled:
                            break

                        # Check if mouse hasn't moved in a while (might be stuck)
                        current_mouse_pos = pyautogui.position()
                        current_time = time.time()
                        
                        # Calculate distance moved since last check
                        mouse_dx = current_mouse_pos[0] - last_mouse_pos[0]
                        mouse_dy = current_mouse_pos[1] - last_mouse_pos[1]
                        movement = (mouse_dx * mouse_dx + mouse_dy * mouse_dy) ** 0.5
                        
                        if movement > MIN_MOVEMENT_THRESHOLD:
                            # Mouse is moving, update tracking time
                            last_mouse_move_time = current_time
                            last_mouse_pos = current_mouse_pos
                        elif current_time - last_mouse_move_time > MOVEMENT_TIMEOUT:
                            # Mouse hasn't moved significantly for a while
                            if current_time - last_detection_reset > MOVEMENT_TIMEOUT * 2:
                                if DEBUG:
                                    print(f"WARNING: Mouse tracking may be frozen - no movement for {current_time - last_mouse_move_time:.1f}s")
                                    print("Attempting to reset detection...")
                                # Force mouse release and reset detection state
                                if mouse_held:
                                    pyautogui.mouseUp(button='left')
                                    mouse_held = False
                                last_ball_rel = None
                                last_ball_time = 0
                                focused_once = False  # Allow another focus click
                                last_detection_reset = current_time
                                # Move to center of region to help reacquire
                                try:
                                    center_x = x + width // 2
                                    center_y = y + height // 2
                                    pyautogui.moveTo(center_x, center_y, duration=0.1)
                                except Exception as e:
                                    if DEBUG:
                                        print(f"Error during reset movement: {e}")

                        # Almost no sleep for maximum responsiveness
                        time.sleep(0.001)

                    # Ensure mouse is released when minigame ends
                    if mouse_held:
                        pyautogui.mouseUp(button='left')
                        mouse_held = False
                    # Move cursor to the middle of the last known slider region so the next
                    # minigame detection starts with the cursor near the bar.
                    try:
                        # slider_center_rel_x is region-relative x of the slider center
                        target_x = int(x + slider_center_rel_x)
                        target_y = int(y + height // 2)
                        if DEBUG:
                            print(f"Moving cursor to last slider center at ({target_x},{target_y})")
                        pyautogui.moveTo(target_x, target_y, duration=0)
                        time.sleep(0.02)
                    except Exception as e:
                        if DEBUG:
                            print(f"Error moving to last slider center: {e}")

                    if DEBUG:
                        print("Minigame ended, waiting 6 seconds to click...")
                    # Wait 6 seconds then click once
                    time.sleep(6)
                    try:
                        if is_bot_enabled:  # Only click if bot is still enabled
                            last_click_pos = pyautogui.position()  # Remember current position
                            pyautogui.click()  # Single click in current position
                            if DEBUG:
                                print(f"Performed post-minigame click at {last_click_pos}")
                    except Exception as e:
                        if DEBUG:
                            print(f"Post-minigame click error: {e}")
                else:
                    # No minigame visible, make sure mouse is released
                    pyautogui.mouseUp()
                    time.sleep(0.05)
            else:
                # Bot is disabled, make sure mouse is released
                pyautogui.mouseUp()
                time.sleep(0.1)  # Reduce CPU usage while bot is disabled
    
    except KeyboardInterrupt:
        print("\nStopping the program...")
    finally:
        # Ensure mouse button is released when script ends
        pyautogui.mouseUp()
        # Destroy any OpenCV windows used for debugging
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass

if __name__ == "__main__":
    # Add a small delay before starting
    print("Starting in 2 seconds...")
    time.sleep(2)
    main()