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
set "USE_GPU=0"
set "INSTALL_SUCCESS=0"

:: ==================== STEP 1: Check Prerequisites ====================
:STEP1
echo.
echo ================================================
echo STEP 1/5: Checking Prerequisites
echo ================================================
echo.

where conda >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Conda not found!
    echo Please install Miniconda or Anaconda first:
    echo https://docs.conda.io/en/latest/miniconda.html
    pause
    exit /b 1
)
echo [OK] Conda found

where git >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git not found!
    echo Please install Git first:
    echo https://git-scm.com/download/win
    pause
    exit /b 1
)
echo [OK] Git found

nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo [INFO] No NVIDIA GPU detected, will use CPU mode
    set "USE_GPU=0"
) else (
    echo [OK] NVIDIA GPU detected
    nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
    set "USE_GPU=1"
)

echo.
echo Press any key to continue...
pause >nul

:: ==================== STEP 2: Create Environment ====================
:STEP2
echo.
echo ================================================
echo STEP 2/5: Creating Conda Environment
echo ================================================
echo.

conda env list 2>&1 | findstr "^%ENV_NAME% " >nul
if not errorlevel 1 (
    echo Environment '%ENV_NAME%' already exists.
    choice /C YN /M "Delete and recreate"
    if errorlevel 2 (
        echo Will use existing environment.
        goto STEP2_DONE
    )
    call conda deactivate >nul 2>&1
    call conda remove -n %ENV_NAME% --all -y
    if errorlevel 1 (
        echo [ERROR] Failed to remove old environment
        pause
        exit /b 1
    )
)

echo Creating conda environment (this may take 2-3 minutes)...
call conda create -n %ENV_NAME% python=%PYTHON_VERSION% -y
if errorlevel 1 (
    echo [ERROR] Failed to create environment
    echo Try: conda clean --all -y
    pause
    exit /b 1
)
echo [OK] Environment created

:STEP2_DONE
echo.
echo Press any key to continue...
pause >nul

:: ==================== STEP 3: Install PyTorch ====================
:STEP3
echo.
echo ================================================
echo STEP 3/5: Installing PyTorch
echo ================================================
echo.

call conda activate %ENV_NAME%
if errorlevel 1 (
    echo [ERROR] Cannot activate environment
    pause
    exit /b 1
)

python -c "import torch" >nul 2>&1
if %errorlevel% == 0 (
    python -c "import torch; print('PyTorch already installed:', torch.__version__)"
    choice /C YN /M "Reinstall PyTorch"
    if errorlevel 2 goto STEP3_DONE
)

echo.
echo Choose PyTorch installation:
echo   [1] CUDA 12.1 (recommended for RTX 30xx/40xx)
echo   [2] CUDA 11.8 (for older GPUs)
echo   [3] CPU only (no GPU)
choice /C 123 /M "Select"

if errorlevel 3 (
    echo Installing CPU version...
    pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cpu
) else if errorlevel 2 (
    echo Installing CUDA 11.8...
    pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu118
) else (
    echo Installing CUDA 12.1...
    pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121
)

if errorlevel 1 (
    echo [WARNING] PyTorch installation may have issues
    choice /C YN /M "Continue anyway"
    if errorlevel 2 exit /b 1
) else (
    echo [OK] PyTorch installed
)

:STEP3_DONE
echo.
echo Press any key to continue...
pause >nul

:: ==================== STEP 4: Install Dependencies ====================
:STEP4
echo.
echo ================================================
echo STEP 4/5: Installing Python Dependencies
echo ================================================
echo.

if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found!
    echo Please make sure you're running this from the VoiceForge directory.
    pause
    exit /b 1
)

echo Installing packages from requirements.txt...
echo This may take 5-10 minutes...
pip install -r requirements.txt

if errorlevel 1 (
    echo [WARNING] Some packages failed to install
    choice /C YN /M "Continue anyway"
    if errorlevel 2 exit /b 1
) else (
    echo [OK] Dependencies installed
)

echo.
echo Press any key to continue...
pause >nul

:: ==================== STEP 5: Download Models ====================
:STEP5
echo.
echo ================================================
echo STEP 5/5: Download AI Models
echo ================================================
echo.

echo AI models are required for VoiceForge to work.
echo.
echo Option 1: Automatic download (from ModelScope)
echo   - SenseVoice (ASR): ~800MB
echo   - CosyVoice (TTS): ~3GB
echo   - Total: ~4GB
echo.
echo Option 2: Manual download
echo   Download from ModelScope website manually
echo.
echo Option 3: Skip for now
echo   You can download later using: python scripts\download_models.py
echo.

choice /C 123 /M "Select option"

if errorlevel 3 (
    echo Skipping model download.
    echo You can download later using: python scripts\download_models.py
) else if errorlevel 2 (
    echo.
    echo Manual download instructions:
    echo 1. SenseVoice: https://modelscope.cn/models/iic/SenseVoiceSmall
    echo    Download to: models\asr\SenseVoiceSmall\
echo.
    echo 2. CosyVoice: https://modelscope.cn/models/iic/CosyVoice-300M-SFT
    echo    Download to: models\tts\CosyVoice-300M-SFT\
echo.
    echo Press any key when ready to continue...
    pause >nul
) else (
    echo.
    echo Starting automatic model download...
    python scripts\download_models.py
    if errorlevel 1 (
        echo.
        echo [WARNING] Model download failed or incomplete.
        echo You can retry later using: python scripts\download_models.py
        pause
    )
)

echo.

:: ==================== FINAL ====================
:FINAL
echo.
echo ================================================
echo Installation Complete!
echo ================================================
echo.

echo [SUCCESS] VoiceForge is ready to use!
echo.
echo Next steps:
echo 1. Make sure models are downloaded:
echo    python scripts\download_models.py
echo.
echo 2. Start VoiceForge:
echo    - API Server: .\scripts\start_api.bat
    echo    - Web UI:     .\scripts\start_web.bat
    echo.
    echo 3. Open browser:
    echo    - Web UI: http://localhost:7860
    echo    - API:    http://localhost:7861
    echo.

    echo Press any key to exit...
    pause >nul
    