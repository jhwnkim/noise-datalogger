@echo off
set PATH=%PATH%;C:\ProgramData\Anaconda3\Scripts
%windir%\system32\cmd.exe "/K" C:\Anaconda3\Scripts\activate.bat noise
hash -r
cd "C:\Users\J Kim\Github\noise-datalogger"
