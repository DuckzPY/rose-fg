@echo off
echo Installing rose-fg dependencies...
echo.
 
python -m pip install --upgrade pip
python -m pip install "qrcode[pil]" Pillow customtkinter python-whois
 
echo.
echo Done.
pause
