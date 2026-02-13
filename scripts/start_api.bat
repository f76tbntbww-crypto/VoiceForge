@echo off
setlocal
chcp 65001 >nul
cls

echo ========================================
echo VoiceForge - API Server
echo ========================================
echo.

cd /d "%~dp0\.."

:: Check .env_name file
if exist ".env_name" (
    set /p ENV_NAME=<.env_name
) else (
    set "ENV_NAME=voiceforge"
)

:: Try to activate Conda environment
call conda activate %ENV_NAME% 2>nul

if errorlevel 1 (
    echo ERROR: Cannot activate Conda environment: %ENV_NAME%
    echo.
    echo Possible reasons:
    echo   1. install.bat has not been run yet
    echo   2. Conda is not properly installed
    echo.
    echo Solutions:
    echo   1. Run .\scripts\install.bat first
    echo   2. Or manually activate: conda activate %ENV_NAME%
    echo.
    pause
    exit /b 1
)

echo OK: Conda environment activated
echo Environment: %CONDA_PREFIX%
python --version
echo.

:: Check if flask is installed
echo Checking dependencies...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Flask is not installed!
    echo.
    echo This usually means Step 4 of install.bat failed.
    echo.
    echo Fix with:
    echo   conda activate %ENV_NAME%
    echo   pip install flask gradio pyyaml numpy requests funasr modelscope soundfile tqdm hyperpyyaml omegaconf torchmetrics
    echo.
    echo Then try again.
    echo.
    pause
    exit /b 1
)

echo OK: Flask installed

:: Check if Matcha-TTS submodule is initialized
if not exist "libs\CosyVoice\third_party\Matcha-TTS\matcha\__init__.py" (
    echo.
    echo ERROR: CosyVoice submodule not initialized!
    echo.
    echo Please run the full installer first:
    echo   .\scripts\install.bat
    echo.
    echo Or manually initialize:
    echo   cd libs\CosyVoice
    echo   git submodule update --init --recursive
    echo.
    pause
    exit /b 1
)

echo OK: CosyVoice submodules ready
echo.

:: Start the server
echo Starting API server...
echo Address: http://localhost:7861
echo Press Ctrl+C to stop
echo.
echo Available endpoints:
echo    GET  /          - Service status
echo    GET  /voices    - Voice list
echo    POST /asr       - Speech recognition
echo    POST /tts       - Speech synthesis
echo    POST /chat      - AI chat
echo    POST /complete  - Complete pipeline
echo.
echo ========================================
echo.

python api\rest_api.py

if errorlevel 1 (
    echo.
    echo ERROR: Server failed to start
    echo    Please check:
    echo      1. Model files exist in models/ directory
    echo      2. config.yaml paths are correct
    echo      3. Ollama is running (for LLM)
    echo.
    pause
)
