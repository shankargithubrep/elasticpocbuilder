#!/bin/bash

# Elastic Demo Builder - Setup Script
# This script creates a virtual environment and installs dependencies

echo "🚀 Setting up Elastic Demo Builder..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create .env from template if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your credentials"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start using the demo builder:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Configure your credentials in .env"
echo "3. Run the app: streamlit run app.py"
echo ""
echo "For the enhanced version with validation:"
echo "   streamlit run app_enhanced.py"