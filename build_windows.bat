@echo off
REM 在 Windows 上一键打包成可双击的 exe（本地备用方案，无需 GitHub）
cd /d "%~dp0"
echo [1/3] 准备环境...
python -m venv .venv 2>nul
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt pyinstaller

echo [2/3] 打包中（--onefile 单文件，首次较慢）...
pyinstaller --noconfirm --clean --onefile --windowed ^
    --name DesktopCat ^
    --add-data "assets;assets" ^
    --icon "assets/cat.ico" ^
    main.py

echo [3/3] 完成！exe 位于 dist\DesktopCat.exe
echo 双击 dist\DesktopCat.exe 即可运行。
pause
