#!/usr/bin/env python3
"""
PDF Table Extractor

A comprehensive tool to extract tables from PDF documents, including:
- Text-based tables using pdfplumber
- Image-based tables using OCR (pytesseract)
- Output to CSV and Excel formats
- Support for multiple table extraction from single PDF
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
from io import BytesIO
import fitz  # PyMuPDF

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PDFTableExtractor:
    """Main class for extracting tables from PDF documents."""
    
    def __init__(self, tesseract_path: Optional[str] = None):
        """
        Initialize the PDF Table Extractor.
        
        Args:
            tesseract_path: Path to tesseract executable (for OCR)
        """
        self.tesseract_path = tesseract_path
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # Check if tesseract is available
        try:
            pytesseract.get_tesseract_version()
            self.ocr_available = True
            logger.info("Tesseract OCR is available")
        except Exception as e:
            self.ocr_available = False
            logger.warning(f"Tesseract OCR not available: {e}")
    
    def extract_tables_from_pdf(self, pdf_path: str, output_dir: str = "output") -> List[str]:
        """
        Extract all tables from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save extracted tables
            
        Returns:
            List of paths to extracted table files
        """
        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        extracted_files = []
        
        try:
            # First, try to extract text-based tables
            text_tables = self._extract_text_tables(pdf_path)
            
            # Then, try to extract image-based tables
            image_tables = self._extract_image_tables(pdf_path)
            
            # Combine and save all tables
            all_tables = text_tables + image_tables
            
            if not all_tables:
                logger.warning("No tables found in the PDF")
                return []
            
            # Save tables to files
            base_name = pdf_path.stem
            for i, table_data in enumerate(all_tables):
                if table_data is not None and not table_data.empty:
                    # Save as CSV
                    csv_path = output_dir / f"{base_name}_table_{i+1}.csv"
                    table_data.to_csv(csv_path, index=False)
                    extracted_files.append(str(csv_path))
                    
                    # Save as Excel
                    excel_path = output_dir / f"{base_name}_table_{i+1}.xlsx"
                    table_data.to_excel(excel_path, index=False)
                    extracted_files.append(str(excel_path))
                    
                    logger.info(f"Extracted table {i+1}: {len(table_data)} rows, {len(table_data.columns)} columns")
            
            return extracted_files
            
        except Exception as e:
            logger.error(f"Error extracting tables from {pdf_path}: {e}")
            return []
    
    def _extract_text_tables(self, pdf_path: Path) -> List[pd.DataFrame]:
        """
        Extract text-based tables using pdfplumber.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of extracted DataFrames
        """
        tables = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    logger.info(f"Processing page {page_num + 1} for text tables")
                    
                    # Extract tables from the page
                    page_tables = page.extract_tables()
                    
                    for table_num, table in enumerate(page_tables):
                        if table and len(table) > 1:  # At least header + one row
                            try:
                                # Convert to DataFrame
                                df = pd.DataFrame(table[1:], columns=table[0])
                                # Clean up the data
                                df = self._clean_dataframe(df)
                                if not df.empty:
                                    tables.append(df)
                                    logger.info(f"Found text table on page {page_num + 1}, table {table_num + 1}")
                            except Exception as e:
                                logger.warning(f"Error processing text table on page {page_num + 1}: {e}")
                                continue
                                
        except Exception as e:
            logger.error(f"Error extracting text tables: {e}")
        
        return tables
    
    def _extract_image_tables(self, pdf_path: Path) -> List[pd.DataFrame]:
        """
        Extract image-based tables using OCR.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of extracted DataFrames
        """
        if not self.ocr_available:
            logger.warning("OCR not available, skipping image table extraction")
            return []
        
        tables = []
        
        try:
            # Open PDF with PyMuPDF to extract images
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                logger.info(f"Processing page {page_num + 1} for image tables")
                
                page = doc[page_num]
                
                # Get images from the page
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    try:
                        # Get image data
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)
                        
                        if pix.n - pix.alpha < 4:  # GRAY or RGB
                            img_data = pix.tobytes("png")
                        else:  # CMYK: convert to RGB
                            pix1 = fitz.Pixmap(fitz.csRGB, pix)
                            img_data = pix1.tobytes("png")
                            pix1 = None
                        
                        # Convert to PIL Image
                        pil_image = Image.open(BytesIO(img_data))
                        
                        # Try to extract table from image
                        table_df = self._extract_table_from_image(pil_image)
                        if table_df is not None and not table_df.empty:
                            tables.append(table_df)
                            logger.info(f"Found image table on page {page_num + 1}, image {img_index + 1}")
                        
                        pix = None
                        
                    except Exception as e:
                        logger.warning(f"Error processing image on page {page_num + 1}: {e}")
                        continue
            
            doc.close()
            
        except Exception as e:
            logger.error(f"Error extracting image tables: {e}")
        
        return tables
    
    def _extract_table_from_image(self, image: Image.Image) -> Optional[pd.DataFrame]:
        """
        Extract table from image using OCR and image processing.
        
        Args:
            image: PIL Image object
            
        Returns:
            DataFrame containing the extracted table, or None if extraction fails
        """
        try:
            # Convert PIL image to OpenCV format
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Preprocess image for better OCR
            processed_image = self._preprocess_image_for_ocr(opencv_image)
            
            # Extract text using OCR
            text = pytesseract.image_to_string(processed_image)
            
            # Try to parse as table
            table_data = self._parse_ocr_text_as_table(text)
            
            if table_data:
                return pd.DataFrame(table_data)
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting table from image: {e}")
            return None
    
    def _preprocess_image_for_ocr(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR results.
        
        Args:
            image: OpenCV image array
            
        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding to get binary image
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Apply morphological operations to clean up
        kernel = np.ones((1, 1), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        return binary
    
    def _parse_ocr_text_as_table(self, text: str) -> Optional[List[List[str]]]:
        """
        Parse OCR text to extract table structure.
        
        Args:
            text: OCR extracted text
            
        Returns:
            List of rows (each row is a list of cells), or None if parsing fails
        """
        try:
            lines = text.strip().split('\n')
            table_data = []
            
            for line in lines:
                line = line.strip()
                if line:
                    # Split by common table separators
                    # Try different separators
                    separators = ['\t', '|', ',', ';', '  ']
                    cells = None
                    
                    for sep in separators:
                        if sep in line:
                            cells = [cell.strip() for cell in line.split(sep) if cell.strip()]
                            break
                    
                    if not cells:
                        # If no separator found, treat the whole line as one cell
                        cells = [line]
                    
                    table_data.append(cells)
            
            # Ensure all rows have the same number of columns
            if table_data:
                max_cols = max(len(row) for row in table_data)
                for i, row in enumerate(table_data):
                    while len(row) < max_cols:
                        row.append('')
                    table_data[i] = row
            
            return table_data if table_data else None
            
        except Exception as e:
            logger.warning(f"Error parsing OCR text as table: {e}")
            return None
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and validate extracted DataFrame.
        
        Args:
            df: Raw DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        try:
            # Remove completely empty rows and columns
            df = df.dropna(how='all').dropna(axis=1, how='all')
            
            # Clean column names
            df.columns = [str(col).strip() if col else f'Column_{i}' 
                         for i, col in enumerate(df.columns)]
            
            # Clean cell values
            for col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                # Remove empty strings
                df[col] = df[col].replace('', np.nan)
            
            # Remove rows where all cells are empty
            df = df.dropna(how='all')
            
            return df
            
        except Exception as e:
            logger.warning(f"Error cleaning DataFrame: {e}")
            return df


def main():
    """Main function to run the PDF table extractor."""
    parser = argparse.ArgumentParser(
        description="Extract tables from PDF files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pdf_table_extractor.py document.pdf
  python pdf_table_extractor.py document.pdf --output-dir ./tables
  python pdf_table_extractor.py document.pdf --tesseract-path /usr/bin/tesseract
        """
    )
    
    parser.add_argument(
        'pdf_path',
        help='Path to the PDF file'
    )
    
    parser.add_argument(
        '--output-dir',
        default='output',
        help='Output directory for extracted tables (default: output)'
    )
    
    parser.add_argument(
        '--tesseract-path',
        help='Path to tesseract executable (for OCR)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if PDF file exists
    if not os.path.exists(args.pdf_path):
        logger.error(f"PDF file not found: {args.pdf_path}")
        sys.exit(1)
    
    # Initialize extractor
    extractor = PDFTableExtractor(tesseract_path=args.tesseract_path)
    
    # Extract tables
    logger.info(f"Extracting tables from: {args.pdf_path}")
    extracted_files = extractor.extract_tables_from_pdf(args.pdf_path, args.output_dir)
    
    if extracted_files:
        logger.info(f"Successfully extracted {len(extracted_files)} table files:")
        for file_path in extracted_files:
            logger.info(f"  - {file_path}")
    else:
        logger.warning("No tables were extracted from the PDF")
        sys.exit(1)


if __name__ == "__main__":
    main()