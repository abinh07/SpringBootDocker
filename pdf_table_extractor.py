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
    
    def __init__(self, tesseract_path: Optional[str] = None, enable_multipage_merge: bool = True):
        """
        Initialize the PDF Table Extractor.
        
        Args:
            tesseract_path: Path to tesseract executable (for OCR)
            enable_multipage_merge: Enable merging of tables spanning multiple pages
        """
        self.tesseract_path = tesseract_path
        self.enable_multipage_merge = enable_multipage_merge
        
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
        
        if enable_multipage_merge:
            logger.info("Multi-page table merging is enabled")
        else:
            logger.info("Multi-page table merging is disabled")
    
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
            if self.enable_multipage_merge:
                text_tables = self._extract_text_tables_with_multipage_support(pdf_path)
            else:
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
    
    def _extract_text_tables_with_multipage_support(self, pdf_path: Path) -> List[pd.DataFrame]:
        """
        Extract text-based tables using pdfplumber with multi-page table support.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of extracted DataFrames
        """
        all_page_tables = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # First pass: collect all tables from all pages
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
                                    all_page_tables.append({
                                        'page': page_num,
                                        'table_num': table_num,
                                        'dataframe': df,
                                        'header': table[0] if table else []
                                    })
                                    logger.info(f"Found text table on page {page_num + 1}, table {table_num + 1}")
                            except Exception as e:
                                logger.warning(f"Error processing text table on page {page_num + 1}: {e}")
                                continue
                                
        except Exception as e:
            logger.error(f"Error extracting text tables: {e}")
            return []
        
        # Second pass: merge multi-page tables
        merged_tables = self._merge_multipage_tables(all_page_tables)
        
        return merged_tables
    
    def _extract_text_tables(self, pdf_path: Path) -> List[pd.DataFrame]:
        """
        Extract text-based tables using pdfplumber (legacy method).
        
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
    
    def _merge_multipage_tables(self, all_page_tables: List[Dict]) -> List[pd.DataFrame]:
        """
        Merge tables that span across multiple pages.
        
        Args:
            all_page_tables: List of dictionaries containing table information
            
        Returns:
            List of merged DataFrames
        """
        if not all_page_tables:
            return []
        
        # Sort tables by page number and table number
        all_page_tables.sort(key=lambda x: (x['page'], x['table_num']))
        
        merged_tables = []
        current_table_group = []
        
        for i, table_info in enumerate(all_page_tables):
            current_df = table_info['dataframe']
            current_header = table_info['header']
            
            # Check if this table should be merged with the previous one
            should_merge = False
            
            if current_table_group:
                # Get the last table in the current group
                last_table_info = current_table_group[-1]
                last_df = last_table_info['dataframe']
                last_header = last_table_info['header']
                
                # Check if headers are similar (indicating same table)
                if self._are_headers_similar(current_header, last_header):
                    # Check if this table appears to be a continuation
                    if self._is_table_continuation(last_df, current_df, last_table_info['page'], table_info['page']):
                        should_merge = True
                        logger.info(f"Merging table from page {table_info['page'] + 1} with table from page {last_table_info['page'] + 1}")
            
            if should_merge:
                # Add to current group
                current_table_group.append(table_info)
            else:
                # Finalize current group if it exists
                if current_table_group:
                    merged_df = self._merge_table_group(current_table_group)
                    if merged_df is not None and not merged_df.empty:
                        merged_tables.append(merged_df)
                        logger.info(f"Merged {len(current_table_group)} table parts into one table with {len(merged_df)} rows")
                
                # Start new group
                current_table_group = [table_info]
        
        # Don't forget the last group
        if current_table_group:
            merged_df = self._merge_table_group(current_table_group)
            if merged_df is not None and not merged_df.empty:
                merged_tables.append(merged_df)
                logger.info(f"Merged {len(current_table_group)} table parts into one table with {len(merged_df)} rows")
        
        return merged_tables
    
    def _are_headers_similar(self, header1: List[str], header2: List[str]) -> bool:
        """
        Check if two table headers are similar enough to be part of the same table.
        
        Args:
            header1: First header
            header2: Second header
            
        Returns:
            True if headers are similar
        """
        if not header1 or not header2:
            return False
        
        # Clean headers
        clean_header1 = [str(h).strip().lower() for h in header1 if str(h).strip()]
        clean_header2 = [str(h).strip().lower() for h in header2 if str(h).strip()]
        
        if len(clean_header1) != len(clean_header2):
            return False
        
        # Check if at least 70% of headers match
        matches = sum(1 for h1, h2 in zip(clean_header1, clean_header2) if h1 == h2)
        similarity = matches / len(clean_header1) if clean_header1 else 0
        
        return similarity >= 0.7
    
    def _is_table_continuation(self, last_df: pd.DataFrame, current_df: pd.DataFrame, 
                              last_page: int, current_page: int) -> bool:
        """
        Check if current table is a continuation of the previous table.
        
        Args:
            last_df: Previous table DataFrame
            current_df: Current table DataFrame
            last_page: Page number of previous table
            current_page: Page number of current table
            
        Returns:
            True if tables appear to be continuations
        """
        # Check if pages are consecutive
        if current_page != last_page + 1:
            return False
        
        # Check if column structure is similar
        if len(last_df.columns) != len(current_df.columns):
            return False
        
        # Check if the last table doesn't end with typical table endings
        # (like totals, summaries, etc.)
        last_row = last_df.iloc[-1] if not last_df.empty else None
        if last_row is not None:
            last_row_str = ' '.join(str(cell).lower() for cell in last_row if pd.notna(cell))
            ending_indicators = ['total', 'sum', 'summary', 'end', 'conclusion', 'final']
            if any(indicator in last_row_str for indicator in ending_indicators):
                return False
        
        # Check if current table doesn't start with typical table headers
        first_row = current_df.iloc[0] if not current_df.empty else None
        if first_row is not None:
            first_row_str = ' '.join(str(cell).lower() for cell in first_row if pd.notna(cell))
            header_indicators = ['total', 'sum', 'summary', 'continued', 'cont.']
            if any(indicator in first_row_str for indicator in header_indicators):
                return True  # This suggests it's a continuation
        
        return True
    
    def _merge_table_group(self, table_group: List[Dict]) -> pd.DataFrame:
        """
        Merge a group of tables into a single DataFrame.
        
        Args:
            table_group: List of table dictionaries to merge
            
        Returns:
            Merged DataFrame
        """
        if not table_group:
            return pd.DataFrame()
        
        # Use the header from the first table
        first_table = table_group[0]
        merged_data = []
        
        for table_info in table_group:
            df = table_info['dataframe']
            
            # Skip header rows for all tables except the first
            if table_info == first_table:
                # Include all rows from first table
                for _, row in df.iterrows():
                    merged_data.append(row.tolist())
            else:
                # Skip potential header row and include data rows
                for i, (_, row) in enumerate(df.iterrows()):
                    # Skip first row if it looks like a header
                    if i == 0 and self._looks_like_header(row, first_table['header']):
                        continue
                    merged_data.append(row.tolist())
        
        if merged_data:
            # Create DataFrame with the header from the first table
            merged_df = pd.DataFrame(merged_data, columns=first_table['header'])
            return self._clean_dataframe(merged_df)
        
        return pd.DataFrame()
    
    def _looks_like_header(self, row: pd.Series, original_header: List[str]) -> bool:
        """
        Check if a row looks like a header row.
        
        Args:
            row: Row to check
            original_header: Original header for comparison
            
        Returns:
            True if row looks like a header
        """
        row_values = [str(cell).strip().lower() for cell in row if pd.notna(cell)]
        header_values = [str(cell).strip().lower() for cell in original_header if pd.notna(cell)]
        
        # Check if row values are similar to header values
        if len(row_values) == len(header_values):
            matches = sum(1 for r, h in zip(row_values, header_values) if r == h)
            similarity = matches / len(row_values) if row_values else 0
            return similarity >= 0.6
        
        return False
    
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
  python pdf_table_extractor.py document.pdf --no-multipage-merge
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
        '--no-multipage-merge',
        action='store_true',
        help='Disable merging of tables spanning multiple pages'
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
    enable_multipage_merge = not args.no_multipage_merge
    extractor = PDFTableExtractor(
        tesseract_path=args.tesseract_path,
        enable_multipage_merge=enable_multipage_merge
    )
    
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