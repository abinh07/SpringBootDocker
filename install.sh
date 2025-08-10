#!/bin/bash

# PDF Table Extractor Installation Script
# This script helps install all dependencies for the PDF table extractor

set -e

echo "🚀 Installing PDF Table Extractor dependencies..."
echo "================================================"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python $PYTHON_VERSION found"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip first."
    exit 1
fi

echo "✅ pip3 found"

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Check for Tesseract OCR
echo ""
echo "🔍 Checking for Tesseract OCR..."

if command -v tesseract &> /dev/null; then
    TESSERACT_VERSION=$(tesseract --version | head -n 1)
    echo "✅ Tesseract found: $TESSERACT_VERSION"
else
    echo "⚠️  Tesseract OCR not found. This is required for image-based table extraction."
    echo ""
    echo "To install Tesseract OCR:"
    echo ""
    echo "Ubuntu/Debian:"
    echo "  sudo apt update"
    echo "  sudo apt install tesseract-ocr tesseract-ocr-eng"
    echo ""
    echo "CentOS/RHEL/Fedora:"
    echo "  sudo yum install tesseract tesseract-langpack-eng"
    echo ""
    echo "macOS:"
    echo "  brew install tesseract"
    echo ""
    echo "Windows:"
    echo "  Download from: https://github.com/UB-Mannheim/tesseract/wiki"
    echo ""
    echo "After installing Tesseract, you can still use the extractor for text-based tables."
fi

# Make scripts executable
echo ""
echo "🔧 Making scripts executable..."
chmod +x pdf_table_extractor.py
chmod +x test_extractor.py

echo ""
echo "✅ Installation completed!"
echo ""
echo "Usage examples:"
echo "  python3 pdf_table_extractor.py document.pdf"
echo "  python3 pdf_table_extractor.py document.pdf --output-dir ./tables"
echo "  python3 test_extractor.py document.pdf"
echo ""
echo "For more information, see README.md"