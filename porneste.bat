@echo off
chcp 65001 >nul
cd /d "%~dp0"
title SKILLIO - nu inchide fereastra asta

rem --- gasesc Python (python, py sau Anaconda) ---
set PY=
where python >nul 2>nul && set PY=python
if not defined PY where py >nul 2>nul && set PY=py
if not defined PY if exist "%USERPROFILE%\anaconda3\python.exe" set PY="%USERPROFILE%\anaconda3\python.exe"
if not defined PY if exist "%USERPROFILE%\miniconda3\python.exe" set PY="%USERPROFILE%\miniconda3\python.exe"
if not defined PY if exist "%ProgramData%\anaconda3\python.exe" set PY="%ProgramData%\anaconda3\python.exe"
if not defined PY if exist "%ProgramData%\miniconda3\python.exe" set PY="%ProgramData%\miniconda3\python.exe"
if not defined PY (
  echo [EROARE] Nu gasesc Python. Instaleaza-l de pe python.org si bifeaza "Add python.exe to PATH".
  pause & exit /b 1
)
echo Folosesc Python: %PY%
%PY% --version

if not exist .venv\Scripts\python.exe (
  echo Creez mediul virtual .venv ...
  %PY% -m venv .venv || (echo [EROARE] Nu am putut crea .venv & pause & exit /b 1)
)
echo Instalez / verific pachetele (prima data dureaza 1-2 minute) ...
.venv\Scripts\python.exe -m pip install --disable-pip-version-check -q -r requirements.txt || (echo [EROARE] Instalarea pachetelor a esuat. Trimite-mi textul de mai sus. & pause & exit /b 1)

start "" cmd /c "timeout /t 8 >nul & start http://localhost:8501/?mod=prezentare"
echo.
echo Aplicatia porneste. Lasa fereastra asta deschisa cat timp prezinti.
.venv\Scripts\python.exe -m streamlit run app.py
echo.
echo Serverul s-a oprit. Daca vezi o eroare mai sus, trimite-mi-o.
pause
