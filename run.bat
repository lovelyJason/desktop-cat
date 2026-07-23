@echo off
REM 在 Windows 上免打包直接运行（需已安装 Python 3.9+）
cd /d "%~dp0"
if not exist ".venv\" (
    echo [1/2] 创建虚拟环境并安装依赖...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)
echo [2/2] 启动桌面猫咪...
python main.py
