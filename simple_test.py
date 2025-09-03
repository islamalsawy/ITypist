#!/usr/bin/env python3

def show_hint(res, hint_text):
    """Simple test version - no external services"""
    x1, y1, x2, y2 = int(res[0]), int(res[1]), int(res[2]), int(res[3])
    
    print("=" * 60)
    print(f"🎯 HINT SUGGESTION FOR EDITTEXT")
    print(f"📍 Position: ({x1},{y1}) → ({x2},{y2})")
    print(f"💡 Suggested hint: '{hint_text}'")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    # Test the function
    test_coords = ['100', '200', '300', '400']
    test_hint = "Enter email"
    
    print("Testing new show_hint function...")
    result = show_hint(test_coords, test_hint)
    print(f"Result: {result}")
    print("✅ Test completed - no FloatingButtonService!")
