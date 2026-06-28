@echo off
chcp 65001 >nul
setlocal

rem 红绳 第一章 完整生成脚本（Windows 批处理入口）
rem 如需国内镜像，取消下面两行注释：
rem set HF_ENDPOINT=https://hf-mirror.com
rem set HF_HUB_ENABLE_HF_TRANSFER=0

set PROJECT_DIR=D:\HermesWorkspace\ai小说\红绳\04-audiobook
set VENV_PYTHON=D:\HermesWorkspace\MOSS-TTS\.venv\Scripts\python.exe
set SCRIPT=%PROJECT_DIR%\scripts\generate_moss_tts_audiobook.py

cd /d "%PROJECT_DIR%"
"%VENV_PYTHON%" "%SCRIPT%" --chapter-dir "%PROJECT_DIR%\ch01_红绳伞"

pause
