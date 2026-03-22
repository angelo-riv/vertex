@echo off
REM Database Migration Windows Batch Wrapper
REM Provides easy access to migration commands with environment setup

setlocal enabledelayedexpansion

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Function to print status messages
:print_status
echo [INFO] %~1
goto :eof

:print_success
echo [SUCCESS] %~1
goto :eof

:print_warning
echo [WARNING] %~1
goto :eof

:print_error
echo [ERROR] %~1
goto :eof

REM Function to check if Python dependencies are installed
:check_dependencies
call :print_status "Checking Python dependencies..."

python -c "import psycopg2" 2>nul
if errorlevel 1 (
    call :print_warning "psycopg2 not found. Installing dependencies..."
    pip install -r requirements.txt
    if errorlevel 1 (
        call :print_error "Failed to install dependencies"
        exit /b 1
    )
)

call :print_success "Dependencies are ready"
goto :eof

REM Function to check database connection
:check_database_connection
call :print_status "Checking database connection..."

python -c "import os; import psycopg2; from migrate import get_database_url; db_url = get_database_url(); conn = psycopg2.connect(db_url); conn.close(); print('Connection successful')" 2>nul
if errorlevel 1 (
    call :print_error "Database connection failed"
    call :print_error "Please check your database configuration and environment variables"
    exit /b 1
)

call :print_success "Database connection verified"
goto :eof

REM Function to show usage
:show_usage
echo Database Migration Tool
echo ======================
echo.
echo Usage: %~nx0 ^<command^> [options]
echo.
echo Commands:
echo   up                    Apply all pending migrations
echo   down ^<migration_id^>   Rollback to specific migration
echo   status                Show migration status
echo   validate              Validate current schema
echo   create ^<name^>         Create new migration file
echo   check                 Check dependencies and database connection
echo   help                  Show this help message
echo.
echo Examples:
echo   %~nx0 up                 # Apply all pending migrations
echo   %~nx0 status             # Show current status
echo   %~nx0 down 002           # Rollback to migration 002
echo   %~nx0 validate           # Validate schema
echo   %~nx0 create "Add new feature"  # Create new migration
echo.
echo Environment Variables:
echo   DATABASE_URL          Full PostgreSQL connection string
echo   DB_HOST               Database host (default: localhost)
echo   DB_PORT               Database port (default: 5432)
echo   DB_NAME               Database name
echo   DB_USER               Database user
echo   DB_PASSWORD           Database password
echo.
goto :eof

REM Function to run migration command
:run_migration
set "command=%~1"
shift
set "args="
:loop_args
if "%~1"=="" goto :end_args
set "args=!args! %~1"
shift
goto :loop_args
:end_args

call :print_status "Running migration command: %command% !args!"

python migrate.py %command% !args!
if errorlevel 1 (
    call :print_error "Migration command failed"
    exit /b 1
)

call :print_success "Migration command completed successfully"
goto :eof

REM Function to run validation
:run_validation
set "args="
:loop_val_args
if "%~1"=="" goto :end_val_args
set "args=!args! %~1"
shift
goto :loop_val_args
:end_val_args

call :print_status "Running schema validation..."

python validate_schema.py !args!
if errorlevel 1 (
    call :print_error "Schema validation failed"
    exit /b 1
)

call :print_success "Schema validation completed"
goto :eof

REM Main script logic
if "%~1"=="" (
    call :show_usage
    exit /b 1
)

set "command=%~1"
shift

if "%command%"=="up" (
    call :check_dependencies
    if errorlevel 1 exit /b 1
    call :check_database_connection
    if errorlevel 1 exit /b 1
    call :run_migration "up" %*
) else if "%command%"=="down" (
    if "%~1"=="" (
        call :print_error "Migration ID required for rollback"
        echo Usage: %~nx0 down ^<migration_id^>
        exit /b 1
    )
    call :check_dependencies
    if errorlevel 1 exit /b 1
    call :check_database_connection
    if errorlevel 1 exit /b 1
    call :run_migration "down" %*
) else if "%command%"=="status" (
    call :check_dependencies
    if errorlevel 1 exit /b 1
    call :check_database_connection
    if errorlevel 1 exit /b 1
    call :run_migration "status" %*
) else if "%command%"=="create" (
    if "%~1"=="" (
        call :print_error "Migration name required"
        echo Usage: %~nx0 create ^<name^>
        exit /b 1
    )
    call :check_dependencies
    if errorlevel 1 exit /b 1
    call :check_database_connection
    if errorlevel 1 exit /b 1
    call :run_migration "create" %*
) else if "%command%"=="validate" (
    call :check_dependencies
    if errorlevel 1 exit /b 1
    call :check_database_connection
    if errorlevel 1 exit /b 1
    call :run_validation %*
) else if "%command%"=="check" (
    call :check_dependencies
    if errorlevel 1 exit /b 1
    call :check_database_connection
    if errorlevel 1 exit /b 1
    call :print_success "All checks passed"
) else if "%command%"=="help" (
    call :show_usage
) else if "%command%"=="-h" (
    call :show_usage
) else if "%command%"=="--help" (
    call :show_usage
) else (
    call :print_error "Unknown command: %command%"
    call :show_usage
    exit /b 1
)

endlocal