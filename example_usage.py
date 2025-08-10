#!/usr/bin/env python3
"""
Example usage of PDF Table Extractor

This script demonstrates how to use the PDFTableExtractor class programmatically
with different configurations and options.
"""

import os
import sys
from pathlib import Path
from pdf_table_extractor import PDFTableExtractor

def example_basic_usage():
    """Example of basic usage."""
    print("=== Basic Usage Example ===")
    
    # Initialize extractor
    extractor = PDFTableExtractor()
    
    # Example PDF path (replace with your actual PDF)
    pdf_path = "sample.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"PDF file '{pdf_path}' not found. Please provide a valid PDF file.")
        return
    
    # Extract tables
    extracted_files = extractor.extract_tables_from_pdf(pdf_path, "basic_output")
    
    print(f"Extracted {len(extracted_files)} files:")
    for file_path in extracted_files:
        print(f"  - {file_path}")

def example_with_custom_tesseract():
    """Example with custom Tesseract path."""
    print("\n=== Custom Tesseract Path Example ===")
    
    # Initialize extractor with custom Tesseract path
    tesseract_path = "/usr/bin/tesseract"  # Adjust this path as needed
    extractor = PDFTableExtractor(tesseract_path=tesseract_path)
    
    pdf_path = "sample.pdf"
    if os.path.exists(pdf_path):
        extracted_files = extractor.extract_tables_from_pdf(pdf_path, "custom_output")
        print(f"Extracted {len(extracted_files)} files with custom Tesseract path")
    else:
        print("PDF file not found for custom Tesseract example")

def example_batch_processing():
    """Example of batch processing multiple PDFs."""
    print("\n=== Batch Processing Example ===")
    
    extractor = PDFTableExtractor()
    
    # Directory containing PDFs
    pdf_directory = "pdfs"
    
    if not os.path.exists(pdf_directory):
        print(f"Directory '{pdf_directory}' not found. Creating example structure...")
        os.makedirs(pdf_directory, exist_ok=True)
        print("Please place your PDF files in the 'pdfs' directory and run again.")
        return
    
    # Process all PDFs in directory
    pdf_files = list(Path(pdf_directory).glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in '{pdf_directory}'")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process:")
    
    for pdf_file in pdf_files:
        print(f"\nProcessing: {pdf_file.name}")
        output_dir = f"batch_output/{pdf_file.stem}"
        
        try:
            extracted_files = extractor.extract_tables_from_pdf(str(pdf_file), output_dir)
            print(f"  Extracted {len(extracted_files)} table files")
        except Exception as e:
            print(f"  Error processing {pdf_file.name}: {e}")

def example_data_analysis():
    """Example of analyzing extracted table data."""
    print("\n=== Data Analysis Example ===")
    
    import pandas as pd
    
    # Check if we have extracted CSV files
    csv_files = list(Path("basic_output").glob("*.csv"))
    
    if not csv_files:
        print("No extracted CSV files found. Run basic usage example first.")
        return
    
    print(f"Analyzing {len(csv_files)} extracted tables:")
    
    for csv_file in csv_files:
        print(f"\n📊 Analyzing: {csv_file.name}")
        
        try:
            df = pd.read_csv(csv_file)
            
            print(f"  Shape: {df.shape}")
            print(f"  Columns: {list(df.columns)}")
            print(f"  Data types:")
            for col, dtype in df.dtypes.items():
                print(f"    {col}: {dtype}")
            
            # Show some statistics for numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                print(f"  Numeric columns statistics:")
                print(df[numeric_cols].describe())
            
            # Show first few rows
            print(f"  First 3 rows:")
            print(df.head(3).to_string(index=False))
            
        except Exception as e:
            print(f"  Error analyzing {csv_file.name}: {e}")

def main():
    """Main function to run all examples."""
    print("PDF Table Extractor - Example Usage")
    print("=" * 40)
    
    # Check if a PDF file was provided as command line argument
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        if os.path.exists(pdf_path):
            # Copy the provided PDF to sample.pdf for examples
            import shutil
            shutil.copy(pdf_path, "sample.pdf")
            print(f"Using provided PDF: {pdf_path}")
        else:
            print(f"Provided PDF file '{pdf_path}' not found.")
            return
    else:
        print("No PDF file provided. Examples will show structure but may not find files.")
        print("Usage: python example_usage.py <path_to_pdf>")
        print()
    
    # Run examples
    example_basic_usage()
    example_with_custom_tesseract()
    example_batch_processing()
    example_data_analysis()
    
    print("\n" + "=" * 40)
    print("Example usage completed!")
    print("\nGenerated files:")
    print("  - basic_output/: Basic extraction results")
    print("  - custom_output/: Custom Tesseract extraction results")
    print("  - batch_output/: Batch processing results")

if __name__ == "__main__":
    main()