@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
cls

cd /d "%~dp0\.."
set "PROJECT_DIR=%CD%"

echo ================================================
echo VoiceForge - One-Click Installer
echo Version: 1.0.0-preview
echo ================================================
echo.
echo Project: %PROJECT_DIR%
echo.
echo This will install everything needed for VoiceForge:
echo  - Python 3.10 environment
echo  - PyTorch with CUDA support
echo  - All Python dependencies
echo.
echo Press any key to start installation...
pause >nul

set "ENV_NAME=voiceforge"
set "PYTHON_VERSION=3.10"

echo.
echo ================================================
echo STEP 1/5: Checking Prerequisites
echo ================================================
echo.

:: Check Conda
echo Checking Conda...

:: Try multiple methods to find conda
set "CONDA_FOUND=0"

:: Method 1: where command
where conda >nul 2>&1
if %errorlevel% equ 0 set "CONDA_FOUND=1"

:: Method 2: check common installation paths
if exist "%UserProfile%\Anaconda3\Scripts\conda.exe" set "CONDA_FOUND=1"
if exist "%UserProfile%\Miniconda3\Scripts\conda.exe" set "CONDA_FOUND=1"
if exist "C:\ProgramData\Anaconda3\Scripts\conda.exe" set "CONDA_FOUND=1"
if exist "C:\ProgramData\Miniconda3\Scripts\conda.exe" set "CONDA_FOUND=1"
if exist "C:\Anaconda3\Scripts\conda.exe" set "CONDA_FOUND=1"
if exist "C:\Miniconda3\Scripts\conda.exe" set "CONDA_FOUND=1"

:: Method 3: check if conda is in PATH via python
python -c "import sys; sys.exit(0 if 'conda' in sys.executable.lower() else 1)" >nul 2>&1
if %errorlevel% equ 0 set "CONDA_FOUND=1"

if %CONDA_FOUND% equ 0 (
    echo.
    echo [ERROR] Conda not found in PATH!
    echo.
    echo Please install Miniconda first:
    echo   https://docs.conda.io/en/latest/miniconda.html
    echo.
    echo IMPORTANT: During installation, check "Add to PATH" option!
    echo.
    echo If already installed, you can:
    echo   1. Reinstall with "Add to PATH" checked
    echo   2. Or manually add to PATH:
    echo      - Open System Properties ^> Advanced ^> Environment Variables
    echo      - Add to PATH: C:\Users\YOURNAME\Miniconda3\Scripts
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)
echo [OK] Conda found

:: Check Ollama
echo.
echo Checking Ollama...
where ollama >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Ollama not detected!
    echo.
    echo Ollama is required to run local LLM.
    echo Download: https://ollama.com/download
    echo.
    set /p continue="Continue without Ollama? (Y/N): "
    if /i "!continue!"=="N" (
        echo.
        echo Installation cancelled. Please install Ollama first.
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
    echo [INFO] Continuing without Ollama
) else (
    echo [OK] Ollama installed
)

:: Check GPU
echo.
echo Checking GPU...
nvidia-smi >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] No NVIDIA GPU detected, will use CPU mode
) else (
    echo [OK] NVIDIA GPU detected
    nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
)

echo.
echo Press any key to continue...
pause >nul

echo.
echo ================================================
echo STEP 2/5: Creating Conda Environment
echo ================================================
echo.

conda env list 2>&1 | findstr "^%ENV_NAME% " >nul
if %errorlevel% equ 0 (
    echo Environment '%ENV_NAME%' already exists.
    set /p recreate="Delete and recreate? (Y/N): "
    if /i "!recreate!"=="Y" (
        call conda deactivate >nul 2>&1
        call conda remove -n %ENV_NAME% --all -y
        if %errorlevel% neq 0 (
            echo [ERROR] Failed to remove old environment
            pause
            exit /b 1
        )
    ) else (
        goto STEP2_DONE
    )
)

echo Creating conda environment...
call conda create -n %ENV_NAME% python=%PYTHON_VERSION% -y
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create environment
    pause
    exit /b 1
)
echo [OK] Environment created

:STEP2_DONE
echo.
echo Press any key to continue...
pause >nul

echo.
echo ================================================
echo STEP 3/5: Installing PyTorch
echo ================================================
echo.

call conda activate %ENV_NAME%
if %errorlevel% neq 0 (
    echo [ERROR] Cannot activate environment
    pause
    exit /b 1
)

python -c "import torch" >nul 2>&1
if %errorlevel% equ 0 (
    python -c "import torch; print('PyTorch already installed:', torch.__version__)"
    set /p reinstall="Reinstall PyTorch? (Y/N): "
    if /i "!reinstall!"=="N" goto STEP3_DONE
)

echo.
echo Choose PyTorch installation:
echo [1] CUDA 12.1 (recommended for RTX 30xx/40xx)
echo [2] CUDA 11.8 (for older GPUs)
echo [3] CPU only (no GPU)
set /p choice="Select (1-3): "

if "!choice!"=="3" (
    echo Installing CPU version...
    pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cpu
) else if "!choice!"=="2" (
    echo Installing CUDA 11.8...
    pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu118
) else (
    echo Installing CUDA 12.1...
    pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121
)

echo [OK] PyTorch installed

:STEP3_DONE
echo.
echo Press any key to continue...
pause >nul

echo.
echo ================================================
echo STEP 4/5: Installing Dependencies
echo ================================================
echo.

if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found!
    pause
    exit /b 1
)

echo Installing packages...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Some packages failed to install
    set /p cont="Continue anyway? (Y/N): "
    if /i "!cont!"=="N" exit /b 1
)
echo [OK] Dependencies installed

echo.
echo Press any key to continue...
pause >nul

echo.
echo ================================================
echo STEP 5/5: Download AI Models
echo ================================================
echo.

echo AI models are required for VoiceForge to work.
echo.
echo [1] Automatic download (from ModelScope)
echo [2] Manual download
echo [3] Skip for now
set /p model_choice="Select (1-3): "

if "!model_choice!"=="3" (
    echo Skipping model download.
    echo You can download later using: python scripts\download_models.py
) else if "!model_choice!"=="2" (
    echo.
    echo Manual download instructions:
    echo 1. SenseVoice: https://modelscope.cn/models/iic/SenseVoiceSmall
    echo    Download to: models\asr\SenseVoiceSmall\
    echo.
    echo 2. CosyVoice: https://modelscope.cn/models/iic/CosyVoice-300M-SFT
    echo    Download to: models\tts\CosyVoice-300M-SFT\
    pause
) else (
    echo.
    echo Starting automatic model download...
    python scripts\download_models.py
    if %errorlevel% neq 0 (
        echo [WARNING] Model download failed.
        echo You can retry later using: python scripts\download_models.py
        pause
    )
)

echo.
echo ================================================
echo Installation Complete!
echo ================================================
echo.
echo [SUCCESS] VoiceForge is ready to use!
echo.
echo Next steps:
echo 1. Start VoiceForge:
echo    - Web UI: .\scripts\start_web.bat
echo    - API Server: .\scripts\start_api.bat
echo.
echo 2. Open browser:
echo    - Web UI: http://localhost:7860
echo.
echo Press any key to exit...
pause >nul
