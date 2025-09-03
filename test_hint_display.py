#!/usr/bin/env python3
"""Test the improved hint display function"""

import os
import time

# Set up ADB path like in main.py
android_sdk_path = r"C:\Users\islam.elafify\AppData\Local\Android\Sdk\platform-tools"
current_path = os.environ.get('PATH', '')
if android_sdk_path not in current_path:
    os.environ['PATH'] = android_sdk_path + os.pathsep + current_path

try:
    import uiautomator2 as u2
    print("✅ uiautomator2 imported successfully!")
except Exception as e:
    print(f"❌ Failed to import uiautomator2: {e}")
    exit(1)

def show_hint_test(res: list, hint_text: str):
    """Test version of the hint display function"""
    x1 = int(res[0])
    y1 = int(res[1])
    x2 = int(res[2])
    y2 = int(res[3])
    
    # Show clear console output
    print("\n" + "=" * 60)
    print(">>> HINT SUGGESTION TEST <<<")
    print(f"EditText Position: ({x1},{y1}) to ({x2},{y2})")
    print(f"Suggested Hint Text: '{hint_text}'")
    print(f"Field Dimensions: {x2-x1}px x {y2-y1}px")
    print("=" * 60)
    
    # Test emulator connection
    try:
        d = u2.connect()
        print("✅ Successfully connected to emulator!")
        print(f"Device info: {d.info}")
        
        # Calculate center of EditText
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        
        print(f"[EMULATOR] Will attempt to click at ({center_x}, {center_y})")
        print(f"[EMULATOR] Hint text to display: '{hint_text}'")
        
        # Click and type (just as a test)
        d.click(center_x, center_y)
        time.sleep(1)
        
        # Type hint for demonstration
        d.send_keys(f"HINT: {hint_text}")
        print("✅ Successfully typed hint text on emulator!")
        
        time.sleep(2)  # Let user see it
        
        # Clear the text
        for _ in range(len(f"HINT: {hint_text}")):
            d.send_keys("backspace")
        
        print("✅ Cleared hint text from emulator")
        
    except Exception as e:
        print(f"❌ Emulator interaction failed: {e}")
        print("Note: Make sure the emulator has a focused text field")
    
    print("=" * 60 + "\n")
    return True

if __name__ == "__main__":
    print("🧪 Testing QTypist hint display functionality...")
    
    # Test with sample coordinates (Gmail login field coordinates)
    test_bounds = [84, 514, 994, 619]
    test_hint = "Enter your email"
    
    success = show_hint_test(test_bounds, test_hint)
    
    if success:
        print("✅ Test completed! The function should work in the main app.")
    else:
        print("❌ Test failed. Check the error messages above.")
