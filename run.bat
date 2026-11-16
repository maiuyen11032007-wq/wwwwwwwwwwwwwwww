@echo off
title SphereAI Agent Server
cd /d "%~dp0"
echo ===================================================================
echo   KHOI DONG HE THONG SPHEREAI AGENT: http://localhost:8080
echo ===================================================================
echo [1/2] Dang mo trinh duyet...
start http://localhost:8080
echo [2/2] May chu FastAPI backend dang hoat dong tren port 8080...
echo.
echo * CHU Y: Giu nguyen cua so den nay de may chu tiep tuc chay lien tuc!
echo ===================================================================
"%~dp0.venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
pause
