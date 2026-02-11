#!/bin/bash

echo "🕉️  WhatsApp Hindu Spiritual Agent - Setup Script"
echo "=================================================="
echo ""

echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then 
    echo "✅ Python $python_version detected"
else
    echo "❌ Python 3.11+ required. Current version: $python_version"
    exit 1
fi

echo ""
echo "Creating virtual environment..."
python3 -m venv venv
echo "✅ Virtual environment created"

echo ""
echo "Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"

echo ""
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✅ Pip upgraded"

echo ""
echo "Installing dependencies (this may take a few minutes)..."
pip install -r requirements.txt > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""
echo "Creating directories..."
mkdir -p logs data/religious_texts data/conversational_data
echo "✅ Directories created"

echo ""
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "✅ .env file created"
    echo "⚠️  Please edit .env and add your API keys"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "Checking PostgreSQL..."
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL found"
    
    read -p "Create database 'hindu_agent_db'? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        createdb hindu_agent_db 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "✅ Database created"
        else
            echo "⚠️  Database may already exist or creation failed"
        fi
    fi
else
    echo "⚠️  PostgreSQL not found. Please install PostgreSQL"
    echo "   Ubuntu/Debian: sudo apt-get install postgresql"
    echo "   macOS: brew install postgresql"
fi

echo ""
echo "Checking Redis..."
if command -v redis-server &> /dev/null; then
    echo "✅ Redis found"
else
    echo "⚠️  Redis not found (optional but recommended)"
    echo "   Ubuntu/Debian: sudo apt-get install redis-server"
    echo "   macOS: brew install redis"
fi

echo ""
read -p "Initialize database tables? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 -c "from utils.database import init_db; init_db()"
    if [ $? -eq 0 ]; then
        echo "✅ Database initialized"
    else
        echo "❌ Database initialization failed"
        echo "   Make sure PostgreSQL is running and .env is configured"
    fi
fi

echo ""
echo "=================================================="
echo "Setup Complete! 🎉"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys:"
echo "   - GOOGLE_API_KEY (Gemini)"
echo "   - OPENAI_API_KEY"
echo "   - PINECONE_API_KEY"
echo "   - MANYCHAT_API_TOKEN"
echo "   - SERPER_API_KEY"
echo ""
echo "2. Download scripture datasets to data/religious_texts/"
echo "   See data/README.md for links"
echo ""
echo "3. Load data into Pinecone:"
echo "   python scripts/load_data.py"
echo ""
echo "4. Run the application:"
echo "   python main.py"
echo ""
echo "5. Setup ManyChat and Make.com:"
echo "   See docs/MANYCHAT_SETUP.md and docs/MAKE_SETUP.md"
echo ""
echo "For help, see README.md or docs/"
echo ""