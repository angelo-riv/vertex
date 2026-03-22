#!/bin/bash
# Database Migration Shell Wrapper
# Provides easy access to migration commands with environment setup

set -e  # Exit on any error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Python dependencies are installed
check_dependencies() {
    print_status "Checking Python dependencies..."
    
    if ! python3 -c "import psycopg2" 2>/dev/null; then
        print_warning "psycopg2 not found. Installing dependencies..."
        pip3 install -r requirements.txt
    fi
    
    print_success "Dependencies are ready"
}

# Function to check database connection
check_database_connection() {
    print_status "Checking database connection..."
    
    if python3 -c "
import os
import psycopg2
from migrate import get_database_url

try:
    db_url = get_database_url()
    conn = psycopg2.connect(db_url)
    conn.close()
    print('Connection successful')
except Exception as e:
    print(f'Connection failed: {e}')
    exit(1)
" 2>/dev/null; then
        print_success "Database connection verified"
    else
        print_error "Database connection failed"
        print_error "Please check your database configuration and environment variables"
        exit 1
    fi
}

# Function to show usage
show_usage() {
    echo "Database Migration Tool"
    echo "======================"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  up                    Apply all pending migrations"
    echo "  down <migration_id>   Rollback to specific migration"
    echo "  status                Show migration status"
    echo "  validate              Validate current schema"
    echo "  create <name>         Create new migration file"
    echo "  check                 Check dependencies and database connection"
    echo "  help                  Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 up                 # Apply all pending migrations"
    echo "  $0 status             # Show current status"
    echo "  $0 down 002           # Rollback to migration 002"
    echo "  $0 validate           # Validate schema"
    echo "  $0 create 'Add new feature'  # Create new migration"
    echo ""
    echo "Environment Variables:"
    echo "  DATABASE_URL          Full PostgreSQL connection string"
    echo "  DB_HOST               Database host (default: localhost)"
    echo "  DB_PORT               Database port (default: 5432)"
    echo "  DB_NAME               Database name"
    echo "  DB_USER               Database user"
    echo "  DB_PASSWORD           Database password"
    echo ""
}

# Function to run migration command
run_migration() {
    local command="$1"
    shift
    
    print_status "Running migration command: $command $*"
    
    if python3 migrate.py "$command" "$@"; then
        print_success "Migration command completed successfully"
        return 0
    else
        print_error "Migration command failed"
        return 1
    fi
}

# Function to run validation
run_validation() {
    print_status "Running schema validation..."
    
    if python3 validate_schema.py "$@"; then
        print_success "Schema validation completed"
        return 0
    else
        print_error "Schema validation failed"
        return 1
    fi
}

# Main script logic
main() {
    if [ $# -eq 0 ]; then
        show_usage
        exit 1
    fi
    
    local command="$1"
    shift
    
    case "$command" in
        "up")
            check_dependencies
            check_database_connection
            run_migration "up" "$@"
            ;;
        "down")
            if [ $# -eq 0 ]; then
                print_error "Migration ID required for rollback"
                echo "Usage: $0 down <migration_id>"
                exit 1
            fi
            check_dependencies
            check_database_connection
            run_migration "down" "$@"
            ;;
        "status")
            check_dependencies
            check_database_connection
            run_migration "status" "$@"
            ;;
        "create")
            if [ $# -eq 0 ]; then
                print_error "Migration name required"
                echo "Usage: $0 create <name>"
                exit 1
            fi
            check_dependencies
            check_database_connection
            run_migration "create" "$@"
            ;;
        "validate")
            check_dependencies
            check_database_connection
            run_validation "$@"
            ;;
        "check")
            check_dependencies
            check_database_connection
            print_success "All checks passed"
            ;;
        "help"|"-h"|"--help")
            show_usage
            ;;
        *)
            print_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"