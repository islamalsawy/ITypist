#!/usr/bin/env python3

# Test script to verify show_hint function
import sys
import os
sys.path.insert(0, r'c:\Users\islam.elafify\Downloads\QTypist-main\source code')

try:
    from main import show_hint
    import inspect
    
    print("=== Testing show_hint function ===")
    
    # Get the source code of the function
    source = inspect.getsource(show_hint)
    
    if 'FloatingButtonService' in source:
        print("❌ ERROR: Found old FloatingButtonService code!")
        print("Function source:")
        print(source)
    elif 'dongzhong' in source:
        print("❌ ERROR: Found old dongzhong service code!")
        print("Function source:")
        print(source)
    else:
        print("✅ Function looks correct - using uiautomator2 approach")
        
        # Test with dummy data
        test_coords = ['100', '200', '300', '400']
        test_hint = "Test hint"
        
        print(f"Testing with coordinates: {test_coords}")
        print(f"Testing with hint: {test_hint}")
        
        # This should not produce any FloatingButtonService errors
        try:
            result = show_hint(test_coords, test_hint)
            print(f"✅ Function executed successfully, returned: {result}")
        except Exception as e:
            print(f"❌ Function failed with error: {e}")

except ImportError as e:
    print(f"❌ Could not import main module: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")

print("\n=== Test completed ===")
