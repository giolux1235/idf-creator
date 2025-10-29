#!/bin/bash
# Railway setup script

echo "🚂 Setting up IDF Creator on Railway..."

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p artifacts/desktop_files/idf
mkdir -p artifacts/desktop_files/docs
mkdir -p artifacts/desktop_files/weather

echo "✅ Setup complete!"

