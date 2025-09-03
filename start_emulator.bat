@echo off
echo Starting Android Emulator...
cd /d "C:\Users\islam.elafify\AppData\Local\Android\Sdk\emulator"
echo.
echo Available AVDs:
emulator.exe -list-avds
echo.
echo Starting Medium_Phone_API_36.0...
emulator.exe -avd Medium_Phone_API_36.0 -no-audio -gpu swiftshader_indirect
pause
