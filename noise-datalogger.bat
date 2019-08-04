@echo off
set PATH=%PATH%;C:\Anaconda3\Scripts
%windir%\system32\cmd.exe "/K" C:\Anaconda3\Scripts\activate.bat noise
cd  "C:\Users\J Kim\Github\noise-datalogger"
python spectrum.py
pause
