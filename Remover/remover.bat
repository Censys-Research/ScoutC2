@echo off
echo Killing process ...
taskkill /F /IM steam2.exe > nul 2>&1

echo Deleting registry key...
reg delete "HKCU\Software\Classes\CLSID\{58149ddf-4ffe-27af-88a0-8e8f9926ede9}" /f > nul 2>&1
reg delete "HKCU\Software\Classes\WOW6432Node\CLSID\{58149ddf-4ffe-27af-88a0-8e8f9926ede9}" /f > nul 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "steam2" /f

echo Deleting folder ...
rmdir /s /q "C:\ProgramData\Vault" > nul 2>&1

echo Done.