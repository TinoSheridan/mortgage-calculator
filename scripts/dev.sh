#!/bin/bash
# Development helper script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3.11+ is available
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
        print_status "Python $PYTHON_VERSION is compatible"
    else
        print_warning "Python $PYTHON_VERSION detected. Python 3.11+ is recommended"
    fi
}

# Setup virtual environment
setup_venv() {
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    print_status "Activating virtual environment..."
    source venv/bin/activate
    
    print_status "Upgrading pip..."
    pip install --upgrade pip
}

# Install dependencies
install_deps() {
    print_status "Installing production dependencies..."
    pip install -r requirements.txt
    
    if [ -f "requirements-dev.txt" ]; then
        print_status "Installing development dependencies..."
        pip install -r requirements-dev.txt
    fi
}

# Setup environment file
setup_env() {
    if [ ! -f ".env" ]; then
        print_status "Creating .env file from template..."
        cp .env.example .env
        print_warning "Please update .env file with your configuration"
    fi
}

# Run code quality checks
quality_check() {
    print_status "Running code quality checks..."
    
    # Black formatting check
    if command -v black &> /dev/null; then
        print_status "Checking code formatting with Black..."
        black --check . || print_warning "Code formatting issues found. Run 'black .' to fix"
    fi
    
    # isort import sorting check
    if command -v isort &> /dev/null; then
        print_status "Checking import sorting with isort..."
        isort --check-only . || print_warning "Import sorting issues found. Run 'isort .' to fix"
    fi
    
    # Flake8 linting
    if command -v flake8 &> /dev/null; then
        print_status "Running flake8 linting..."
        flake8 . || print_warning "Linting issues found"
    fi
}

# Run tests
run_tests() {
    print_status "Running tests..."
    if command -v pytest &> /dev/null; then
        pytest -v --cov=. --cov-report=html
        print_status "Test coverage report generated in htmlcov/"
    else
        python -m unittest discover tests/
    fi
}

# Start development server
start_dev() {
    print_status "Starting development server..."
    export FLASK_ENV=development
    export FLASK_DEBUG=1
    python app_refactored.py
}

# Main function
main() {
    case $1 in
        "setup")
            print_status "Setting up development environment..."
            check_python
            setup_venv
            install_deps
            setup_env
            print_status "Development environment setup complete!"
            ;;
        "install")
            setup_venv
            install_deps
            ;;
        "check")
            quality_check
            ;;
        "test")
            run_tests
            ;;
        "run")
            start_dev
            ;;
        "format")
            print_status "Formatting code..."
            black .
            isort .
            print_status "Code formatting complete!"
            ;;
        "clean")
            print_status "Cleaning up..."
            find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
            find . -name "*.pyc" -delete
            find . -name "*.pyo" -delete
            rm -rf .pytest_cache
            rm -rf htmlcov/
            print_status "Cleanup complete!"
            ;;
        *)
            echo "Usage: $0 {setup|install|check|test|run|format|clean}"
            echo ""
            echo "Commands:"
            echo "  setup   - Set up complete development environment"
            echo "  install - Install dependencies"
            echo "  check   - Run code quality checks"
            echo "  test    - Run tests with coverage"
            echo "  run     - Start development server"
            echo "  format  - Format code with black and isort"
            echo "  clean   - Clean up cache files"
            exit 1
            ;;
    esac
}

main $1