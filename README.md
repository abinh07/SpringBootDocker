# PDF Table Extractor

A comprehensive Python tool to extract tables from PDF documents, including both text-based tables and image-based tables using OCR technology.

## Features

- **Text-based table extraction**: Uses `pdfplumber` to extract tables that are embedded as text in PDFs
- **Image-based table extraction**: Uses OCR (Tesseract) to extract tables from images within PDFs
- **Multiple output formats**: Exports tables to both CSV and Excel formats
- **Robust error handling**: Gracefully handles various PDF formats and extraction scenarios
- **Comprehensive logging**: Detailed logging for debugging and monitoring
- **Command-line interface**: Easy-to-use CLI with various options

## Installation

### Prerequisites

1. **Python 3.7+** is required
2. **Tesseract OCR** (for image-based table extraction)

### Install Tesseract OCR

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install tesseract-ocr
sudo apt install tesseract-ocr-eng  # English language pack
```

#### CentOS/RHEL/Fedora:
```bash
sudo yum install tesseract
sudo yum install tesseract-langpack-eng  # English language pack
```

#### macOS:
```bash
brew install tesseract
```

#### Windows:
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

### Install Python Dependencies

1. Clone or download this repository
2. Install the required Python packages:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Extract all tables from a PDF file:

```bash
python pdf_table_extractor.py document.pdf
```

### Advanced Usage

```bash
# Specify output directory
python pdf_table_extractor.py document.pdf --output-dir ./extracted_tables

# Specify Tesseract path (if not in system PATH)
python pdf_table_extractor.py document.pdf --tesseract-path /usr/bin/tesseract

# Enable verbose logging
python pdf_table_extractor.py document.pdf --verbose

# Combine options
python pdf_table_extractor.py document.pdf --output-dir ./tables --verbose
```

### Command Line Options

- `pdf_path`: Path to the PDF file (required)
- `--output-dir`: Output directory for extracted tables (default: `output`)
- `--tesseract-path`: Path to tesseract executable (for OCR)
- `--verbose`: Enable verbose logging

## Output

The script creates the following files for each extracted table:

- `{pdf_name}_table_1.csv` - CSV format
- `{pdf_name}_table_1.xlsx` - Excel format
- `{pdf_name}_table_2.csv` - CSV format (if multiple tables)
- `{pdf_name}_table_2.xlsx` - Excel format (if multiple tables)

## How It Works

### Text-based Table Extraction

1. Uses `pdfplumber` to parse PDF structure
2. Identifies table elements in the PDF
3. Extracts text content from table cells
4. Converts to pandas DataFrame
5. Cleans and validates the data

### Image-based Table Extraction

1. Uses `PyMuPDF` to extract images from PDF pages
2. Preprocesses images using OpenCV for better OCR
3. Uses Tesseract OCR to extract text from images
4. Parses the OCR text to identify table structure
5. Converts to pandas DataFrame

### Data Cleaning

- Removes empty rows and columns
- Cleans column names
- Strips whitespace from cell values
- Handles missing data appropriately

## Examples

### Example 1: Simple PDF with text tables

```bash
python pdf_table_extractor.py financial_report.pdf
```

Output:
```
2024-01-15 10:30:15 - INFO - Tesseract OCR is available
2024-01-15 10:30:15 - INFO - Extracting tables from: financial_report.pdf
2024-01-15 10:30:16 - INFO - Processing page 1 for text tables
2024-01-15 10:30:16 - INFO - Found text table on page 1, table 1
2024-01-15 10:30:16 - INFO - Extracted table 1: 25 rows, 5 columns
2024-01-15 10:30:16 - INFO - Successfully extracted 2 table files:
2024-01-15 10:30:16 - INFO -   - output/financial_report_table_1.csv
2024-01-15 10:30:16 - INFO -   - output/financial_report_table_1.xlsx
```

### Example 2: PDF with image-based tables

```bash
python pdf_table_extractor.py scanned_document.pdf --verbose
```

Output:
```
2024-01-15 10:35:20 - INFO - Tesseract OCR is available
2024-01-15 10:35:20 - INFO - Extracting tables from: scanned_document.pdf
2024-01-15 10:35:21 - INFO - Processing page 1 for text tables
2024-01-15 10:35:21 - INFO - Processing page 1 for image tables
2024-01-15 10:35:22 - INFO - Found image table on page 1, image 1
2024-01-15 10:35:22 - INFO - Extracted table 1: 12 rows, 4 columns
2024-01-15 10:35:22 - INFO - Successfully extracted 2 table files:
2024-01-15 10:35:22 - INFO -   - output/scanned_document_table_1.csv
2024-01-15 10:35:22 - INFO -   - output/scanned_document_table_1.xlsx
```

## Troubleshooting

### Common Issues

1. **Tesseract not found**
   ```
   TesseractNotFoundError: tesseract is not installed or it's not in your PATH
   ```
   Solution: Install Tesseract OCR or specify the path using `--tesseract-path`

2. **No tables extracted**
   - Check if the PDF actually contains tables
   - Try with `--verbose` flag for more detailed logging
   - Ensure the PDF is not corrupted

3. **Poor OCR results**
   - Ensure the image quality is good
   - Try preprocessing the PDF images manually
   - Check if the table structure is clear in the image

4. **Memory issues with large PDFs**
   - Process PDFs page by page
   - Consider splitting large PDFs into smaller files

### Performance Tips

- For large PDFs, consider processing them in batches
- OCR processing can be slow for image-heavy PDFs
- Text-based extraction is much faster than OCR-based extraction

## Dependencies

- `pandas`: Data manipulation and CSV/Excel export
- `pdfplumber`: PDF text extraction
- `Pillow`: Image processing
- `pytesseract`: OCR functionality
- `opencv-python`: Image preprocessing
- `numpy`: Numerical operations
- `PyMuPDF`: PDF image extraction
- `openpyxl`: Excel file writing

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions, please:

1. Check the troubleshooting section above
2. Enable verbose logging with `--verbose` flag
3. Check the logs for specific error messages
4. Open an issue with detailed information about your problem