@echo off
cd /d "%~dp0"
if not exist .venv (
  echo Creez mediul virtual si instalez pachetele...
  python -m venv .venv
  call .venv\Scripts\activate
  pip install -r requirements.txt
) else (
  call .venv\Scripts\activate
)
start "" cmd /c "timeout /t 8 >/dev/null & start http://localhost:8501/?mod=prezentare"
streamlit run app.py
