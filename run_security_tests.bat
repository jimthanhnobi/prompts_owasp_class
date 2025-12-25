@echo off
echo ========================================
echo MoneyCare Security Tests (OWASP LLM Top 10)
echo ========================================
echo.

python run_tests.py -f test_cases_security.json --export excel --priority Critical

echo.
echo Test completed! Check test_results folder
pause
