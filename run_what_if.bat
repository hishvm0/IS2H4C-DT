@echo off
REM What-If Energy Calculator Launcher for Windows
REM Starts the Streamlit what-if calculator app

echo Starting What-If Energy Calculator...
echo.

cd dashboard
streamlit run what_if_calculator.py --server.port 8502
