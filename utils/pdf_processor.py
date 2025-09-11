import PyPDF2
import os
from .preprocessing import clean_text
import re

class PDFProcessor:
    def __init__(self):
        pass

    def extract_text_from_pdf(self, pdf_file):
        """Extract text content from PDF file with improved error handling"""
        pdf_reader = None
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            # Check if PDF has pages
            if len(pdf_reader.pages) == 0:
                raise Exception("PDF appears to be empty or corrupted")

            # Extract text from all pages with progress tracking
            text_content = []
            total_pages = len(pdf_reader.pages)

            for i, page in enumerate(pdf_reader.pages):
                try:
                    text = page.extract_text()
                    if text and text.strip():  # Only add non-empty pages
                        text_content.append(text)
                except Exception as e:
                    print(f"Warning: Could not extract text from page {i+1}: {e}")
                    continue

            if not text_content:
                raise Exception("No readable text found in PDF")

            full_text = '\n\n'.join(text_content)

            # Clean and preprocess the extracted text
            cleaned_text = self._post_process_pdf_text(full_text)

            return cleaned_text

        except PyPDF2.errors.PdfReadError as e:
            raise Exception(f"Invalid or corrupted PDF file: {str(e)}")
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
        finally:
            # Ensure PDF reader is properly closed
            if pdf_reader:
                try:
                    pdf_reader.stream.close()
                except:
                    pass

    def _post_process_pdf_text(self, text):
        """Clean and normalize text extracted from PDFs"""
        if not text:
            return ""

        # Remove excessive whitespace and line breaks
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r' +', ' ', text)

        # Fix common PDF extraction issues
        text = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', text)  # Fix hyphenated words
        text = re.sub(r'(\w)\s*\n\s*(?![A-Z])', r'\1 ', text)  # Fix line breaks in sentences

        # Remove page headers/footers (common patterns)
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)  # Page numbers
        text = re.sub(r'^.*?(?=Abstract|Introduction|Chapter|Section)', '', text,
                     flags=re.MULTILINE | re.IGNORECASE)

        # Apply standard text cleaning
        text = clean_text(text)

        return text

    def get_pdf_metadata(self, pdf_file):
        """Extract metadata from PDF"""
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            metadata = pdf_reader.metadata

            return {
                'title': metadata.get('/Title', 'Unknown'),
                'author': metadata.get('/Author', 'Unknown'),
                'pages': len(pdf_reader.pages),
                'size': len(pdf_file.read()) if hasattr(pdf_file, 'read') else 'Unknown'
            }
        except:
            return {
                'title': 'Unknown',
                'author': 'Unknown',
                'pages': 'Unknown',
                'size': 'Unknown'
            }

    def validate_pdf(self, pdf_file):
        """Validate if the uploaded file is a valid PDF"""
        try:
            # Check file extension
            if hasattr(pdf_file, 'filename'):
                filename = pdf_file.filename.lower()
                if not filename.endswith('.pdf'):
                    return False, "File must be a PDF"

            # Try to read as PDF
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            # Check if it has pages
            if len(pdf_reader.pages) == 0:
                return False, "PDF appears to be empty"

            return True, "Valid PDF"

        except PyPDF2.errors.PdfReadError:
            return False, "Invalid or corrupted PDF file"
        except Exception as e:
            return False, f"Error validating PDF: {str(e)}"