#!/bin/bash

# Financial Document Analyzer Setup Script
# This script sets up the environment and dependencies

set -e  # Exit on any error

echo "🚀 Setting up Financial Document Analyzer..."

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

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

print_success "Python 3 found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed. Please install pip first."
    exit 1
fi

print_success "pip3 found: $(pip3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install requirements
print_status "Installing core requirements..."
pip install -r requirements.txt

print_success "Core dependencies installed successfully!"

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p data
mkdir -p output
mkdir -p logs

# Create .env file from template if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.template" ]; then
        print_status "Creating .env file from template..."
        cp .env.template .env
        print_warning "Please edit .env file with your API keys!"
    else
        print_status "Creating basic .env file..."
        cat > .env << EOF
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Serper Dev API Configuration (for web search functionality)
SERPER_API_KEY=your_serper_api_key_here

# Application Configuration
APP_ENV=development
LOG_LEVEL=INFO
EOF
        print_warning "Please edit .env file with your API keys!"
    fi
else
    print_status ".env file already exists"
fi

# Optional: Install bonus features
read -p "Do you want to install Redis Queue support? (y/n): " install_redis
if [ "$install_redis" = "y" ] || [ "$install_redis" = "Y" ]; then
    print_status "Installing Redis Queue dependencies..."
    pip install redis==5.0.7 rq==1.16.1
    print_success "Redis Queue support installed!"
    print_warning "Make sure Redis server is running for queue functionality"
else
    print_status "Skipping Redis Queue installation"
fi

# Optional: Install database support
read -p "Do you want to install database support? (y/n): " install_db
if [ "$install_db" = "y" ] || [ "$install_db" = "Y" ]; then
    echo "Choose database type:"
    echo "1) SQLite (recommended for development)"
    echo "2) PostgreSQL (recommended for production)"
    echo "3) MySQL"
    read -p "Enter choice (1-3): " db_choice
    
    case $db_choice in
        1)
            print_status "SQLite support already included in core requirements"
            ;;
        2)
            print_status "Installing PostgreSQL dependencies..."
            pip install psycopg2-binary==2.9.9
            print_success "PostgreSQL support installed!"
            ;;
        3)
            print_status "Installing MySQL dependencies..."
            pip install pymysql==1.1.0
            print_success "MySQL support installed!"
            ;;
        *)
            print_warning "Invalid choice, defaulting to SQLite"
            ;;
    esac
    
    # Install Alembic for database migrations
    pip install alembic==1.13.1
    print_success "Database migration tools installed!"
else
    print_status "Skipping database installation"
fi

# Test the installation
print_status "Testing the installation..."

# Test imports
python3 -c "
import fastapi
import crewai
import openai
print('✅ Core dependencies working')
" 2>/dev/null && print_success "Core dependencies test passed" || print_error "Core dependencies test failed"

# Check if .env file has been configured
if grep -q "your_openai_api_key_here" .env; then
    print_warning "⚠️  IMPORTANT: You need to configure your API keys in .env file!"
    print_status "Required API keys:"
    print_status "  - OPENAI_API_KEY (required)"
    print_status "  - SERPER_API_KEY (optional, for web search)"
else
    print_success "API keys appear to be configured"
fi

# Create a sample test file
print_status "Creating sample test document..."
if [ ! -f "data/sample.pdf" ]; then
    print_warning "No sample PDF found. Please add a financial PDF as 'data/sample.pdf' for testing."
    print_status "You can:"
    print_status "  1. Download Tesla's Q2 2025 report from Tesla's investor relations"
    print_status "  2. Use any financial PDF document"
    print_status "  3. Upload files via the API endpoints"
fi

# Display next steps
print_success "🎉 Setup completed successfully!"
echo
echo "📋 Next steps:"
echo "  1. Edit .env file with your API keys"
echo "  2. Add a sample PDF to data/sample.pdf (optional)"
echo "  3. Start the application:"
echo "     python main.py"
echo
echo "🌐 Once running, visit:"
echo "  - API: http://localhost:8000"
echo "  - Docs: http://localhost:8000/docs"
echo "  - Health: http://localhost:8000/health"
echo
echo "🔧 Development commands:"
echo "  - Start server: python main.py"
echo "  - Run worker (if Redis installed): python redis_queue.py worker"
echo "  - Initialize DB (if database installed): python database.py"
echo
print_success "Happy analyzing! 📊"

# Optional: Start the server
echo
read -p "Do you want to start the server now? (y/n): " start_server
if [ "$start_server" = "y" ] || [ "$start_server" = "Y" ]; then
    if grep -q "your_openai_api_key_here" .env; then
        print_error "Please configure your API keys first!"
        exit 1
    fi
    
    print_status "Starting the Financial Document Analyzer..."
    python main.py
fi