@echo off
echo ========================================
echo MoneyCare Chatbot Test Framework
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Install dependencies if needed
echo Installing dependencies...
pip install -r requirements.txt -q

echo.
echo ========================================
echo Running Functional Tests
echo ========================================
python run_tests.py -f test_cases.json --export excel

echo.
echo ========================================
echo Running Security Tests (OWASP)
echo ========================================
python run_tests.py -f test_cases_security.json --export excel

echo.
echo ========================================
echo Running C-L-A-S-S Metrics Tests
echo ========================================
python run_tests.py -f test_cases_classs.json --export excel

echo.
echo ========================================
echo Running CLASS Design Tests
echo ========================================
python run_tests.py -f test_cases_class_design.json --export excel

echo.
echo ========================================
echo All tests completed!
echo Check test_results folder for reports
echo ========================================
pause
