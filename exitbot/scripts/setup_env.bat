@echo off
setlocal enabledelayedexpansion

REM Setup script for ExitBot deployment on Windows

REM Parse arguments
set "ENVIRONMENT=development"
set "LLM_PROVIDER=groq"

:parse_args
if "%~1"=="" goto :end_parse_args
if "%~1"=="-h" goto :show_help
if "%~1"=="--help" goto :show_help
if "%~1"=="-p" set "ENVIRONMENT=production" & goto :next_arg
if "%~1"=="--prod" set "ENVIRONMENT=production" & goto :next_arg
if "%~1"=="-d" set "ENVIRONMENT=development" & goto :next_arg
if "%~1"=="--dev" set "ENVIRONMENT=development" & goto :next_arg
if "%~1"=="-g" set "LLM_PROVIDER=groq" & goto :next_arg
if "%~1"=="--groq" set "LLM_PROVIDER=groq" & goto :next_arg
if "%~1"=="-o" set "LLM_PROVIDER=ollama" & goto :next_arg
if "%~1"=="--ollama" set "LLM_PROVIDER=ollama" & goto :next_arg
echo Unknown option: %~1
goto :show_help

:next_arg
shift
goto :parse_args

:end_parse_args

REM Create .env file from template if it doesn't exist
if not exist .env (
    echo Creating .env file from template...
    copy .env.template .env
    echo .env file created. Please update SECRET_KEY to a secure random value.
) else (
    echo .env file already exists. Skipping...
)

REM Print environment info
echo Environment: %ENVIRONMENT%
echo LLM Provider: %LLM_PROVIDER%

REM Create required directories
if not exist nginx\ssl mkdir nginx\ssl
if not exist nginx\conf.d mkdir nginx\conf.d
if not exist logs mkdir logs

echo Environment setup complete!
echo To start the application in %ENVIRONMENT% mode, run:
if "%ENVIRONMENT%"=="production" (
    echo   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
) else (
    echo   docker-compose up -d
)

goto :eof

:show_help
echo ExitBot Setup Script
echo Usage: %0 [options]
echo.
echo Options:
echo   -h, --help       Show this help message
echo   -p, --prod       Set up production environment
echo   -d, --dev        Set up development environment (default)
echo   -g, --groq       Use Groq as LLM provider
echo   -o, --ollama     Use Ollama as LLM provider
echo.
exit /b 