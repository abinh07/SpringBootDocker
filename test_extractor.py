#!/usr/bin/env python3
"""
Test script for PDF Table Extractor

This script demonstrates how to use the PDFTableExtractor class programmatically.
"""

import os
import sys
from pdf_table_extractor import PDFTableExtractor

def test_extractor():
    """Test the PDF table extractor with a sample PDF."""
    
    # Check if a PDF file was provided as command line argument
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        print("Usage: python test_extractor.py <path_to_pdf>")
        print("Example: python test_extractor.py sample.pdf")
        return
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file '{pdf_path}' not found.")
        return
    
    print(f"Testing PDF Table Extractor with: {pdf_path}")
    print("-" * 50)
    
    # Initialize the extractor
    extractor = PDFTableExtractor()
    
    # Extract tables
    try:
        extracted_files = extractor.extract_tables_from_pdf(pdf_path, "test_output")
        
        if extracted_files:
            print(f"\n✅ Successfully extracted {len(extracted_files)} table files:")
            for file_path in extracted_files:
                print(f"  📄 {file_path}")
            
            # Show a preview of the first CSV file
            csv_files = [f for f in extracted_files if f.endswith('.csv')]
            if csv_files:
                print(f"\n📊 Preview of first table ({csv_files[0]}):")
                import pandas as pd
                df = pd.read_csv(csv_files[0])
                print(f"Shape: {df.shape}")
                print("First few rows:")
                print(df.head())
                
        else:
            print("\n❌ No tables were extracted from the PDF.")
            print("This could mean:")
            print("  - The PDF doesn't contain tables")
            print("  - The tables are in a format not recognized by the extractor")
            print("  - Try running with --verbose flag for more details")
            
    except Exception as e:
        print(f"\n❌ Error during extraction: {e}")
        print("Please check:")
        print("  - PDF file is not corrupted")
        print("  - All dependencies are installed")
        print("  - Tesseract OCR is available (for image-based tables)")

if __name__ == "__main__":
    test_extractor()