import os
android_sdk_path = r"C:\Users\islam.elafify\AppData\Local\Android\Sdk\platform-tools"
current_path = os.environ.get('PATH', '')
os.environ['PATH'] = android_sdk_path + os.pathsep + current_path

print("Testing hint display...")
print("=" * 50)
print(">>> HINT SUGGESTION <<<")
print("Position: (84,514) to (994,619)")
print("Suggested Hint: 'Enter your email'")
print("Dimensions: 910px x 105px")
print("=" * 50)
print("✅ Console output test completed!")
