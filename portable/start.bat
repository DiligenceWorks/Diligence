@echo off
:: ============================================================================
:: Diligence — Self-hosted fitness rewards platform
:: Double-click this file to start. Your browser will open automatically.
:: Press Ctrl+C in this window to stop.
:: ============================================================================
title Diligence

:: Get the directory this script lives in
set "APP_DIR=%~dp0"

:: Data lives alongside the app (portable — no files outside this folder)
set "DATA_DIR=%APP_DIR%data"

:: Tell Python where to find the app and its dependencies
:: (The ._pth file handles most of this, but DATA_DIR needs an env var)
set "DATA_DIR=%DATA_DIR%"

echo.
echo   Diligence
echo   =========
echo.
echo   Starting up... (this may take 10-30 seconds on first run)
echo   Your browser will open automatically.
echo.
echo   Data folder: %DATA_DIR%
echo   Press Ctrl+C to stop.
echo.

:: Run the app using the bundled Python
"%APP_DIR%python\python.exe" -m diligence --data-dir "%DATA_DIR%" %*

:: If we get here, the app exited
echo.
echo   Diligence has stopped.
pause
