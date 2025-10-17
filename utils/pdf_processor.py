import PyPDF2
import os
from .preprocessing import clean_text
import re
from typing import Optional, Dict, Any
import logging
import io

# Set up logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import PyMuPDF, but don't fail if not available
try:
    import fitz  # PyMuPDF for better PDF processing
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    logger.warning("PyMuPDF not available - using PyPDF2 fallback")


class PDFProcessor:
    def __init__(self):
        self.use_pymupdf = False  # Disable PyMuPDF until installed
        self.fallback_to_pypdf2 = True
        self._check_dependencies()

    def _check_dependencies(self):
        """Check available dependencies and configure accordingly"""
        global HAS_PYMUPDF
        self.use_pymupdf = HAS_PYMUPDF

        if HAS_PYMUPDF:
            logger.info("PyMuPDF available - enhanced PDF processing enabled")
        else:
            logger.warning("PyMuPDF not available - using PyPDF2 fallback")

    def extract_text_from_pdf(self, pdf_file) -> str:
        """Extract text content from PDF file with enhanced extraction methods"""
        logger.info("Starting PDF text extraction...")

        # Try PyMuPDF first (better extraction)
        if self.use_pymupdf:
            try:
                text = self._extract_with_pymupdf(pdf_file)
                if text and len(text.strip()) > 100:  # Ensure we got substantial text
                    logger.info(f"Successfully extracted {len(text)} characters using PyMuPDF")
                    return self._post_process_pdf_text(text)
            except ImportError:
                logger.warning("PyMuPDF not available, falling back to PyPDF2")
            except Exception as e:
                logger.warning(f"PyMuPDF extraction failed: {e}, trying PyPDF2")

        # Fallback to PyPDF2
        if self.fallback_to_pypdf2:
            try:
                text = self._extract_with_pypdf2(pdf_file)
                if text and len(text.strip()) > 50:
                    logger.info(f"Successfully extracted {len(text)} characters using PyPDF2")
                    return self._post_process_pdf_text(text)
            except Exception as e:
                logger.error(f"PyPDF2 extraction also failed: {e}")

        # Try OCR as last resort for scanned PDFs
        if self.fallback_to_pypdf2:
            try:
                logger.info("Attempting OCR extraction for scanned PDF...")
                ocr_text = self._extract_with_ocr(pdf_file)
                if ocr_text and len(ocr_text.strip()) > 100:
                    logger.info(f"Successfully extracted {len(ocr_text)} characters using OCR")
                    return self._post_process_pdf_text(ocr_text)
            except Exception as e:
                logger.warning(f"OCR extraction failed: {e}")

        raise Exception("Could not extract readable text from PDF using any available method")

    def _extract_with_pymupdf(self, pdf_file) -> str:
        """Extract text using PyMuPDF (better for complex layouts)"""
        if not HAS_PYMUPDF:
            raise ImportError("PyMuPDF not available")

        try:

            # Reset file pointer if needed
            if hasattr(pdf_file, 'seek'):
                pdf_file.seek(0)

            doc = fitz.open(stream=pdf_file.read(), filetype="pdf")

            if doc.page_count == 0:
                raise Exception("PDF appears to be empty")

            text_content = []
            for page_num in range(doc.page_count):
                try:
                    page = doc.load_page(page_num)
                    # Use better extraction method for PyMuPDF
                    text = page.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE)

                    if text and text.strip():
                        text_content.append(text)
                except Exception as e:
                    logger.warning(f"Could not extract text from page {page_num + 1}: {e}")
                    continue

            if not text_content:
                raise Exception("No readable text found in PDF")

            return '\n\n'.join(text_content)

        except ImportError:
            raise ImportError("PyMuPDF (fitz) is not installed")

    def _extract_with_pypdf2(self, pdf_file) -> str:
        """Extract text using PyPDF2 with enhanced processing"""
        pdf_reader = None
        try:
            # Reset file pointer if needed
            if hasattr(pdf_file, 'seek'):
                pdf_file.seek(0)

            pdf_reader = PyPDF2.PdfReader(pdf_file)

            if len(pdf_reader.pages) == 0:
                raise Exception("PDF appears to be empty or corrupted")

            text_content = []
            total_pages = len(pdf_reader.pages)

            for i, page in enumerate(pdf_reader.pages):
                try:
                    # Enhanced text extraction
                    text = page.extract_text()

                    # Try alternative extraction if main method fails
                    if not text or len(text.strip()) < 50:
                        # Try extracting in sections
                        text = self._extract_page_sections(page)

                    if text and text.strip():
                        text_content.append(text)
                except Exception as e:
                    logger.warning(f"Could not extract text from page {i+1}: {e}")
                    continue

            if not text_content:
                raise Exception("No readable text found in PDF")

            return '\n\n'.join(text_content)

        except PyPDF2.errors.PdfReadError as e:
            raise Exception(f"Invalid or corrupted PDF file: {str(e)}")
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
        finally:
            if pdf_reader:
                try:
                    pdf_reader.stream.close()
                except:
                    pass

    def _extract_page_sections(self, page) -> str:
        """Try to extract text in sections if main extraction fails"""
        try:
            # Try different extraction methods
            text = ""

            # Method 1: Extract by character positions
            try:
                if hasattr(page, 'extract_text'):
                    text = page.extract_text()
            except:
                pass

            # Method 2: Try to get text fragments
            if not text and hasattr(page, 'get_contents'):
                try:
                    contents = page.get_contents()
                    if contents:
                        # This is a fallback method for difficult PDFs
                        text = f"[Page {page.page_number}] Content extracted with fallback method"
                except:
                    pass

            return text
        except:
            return ""

    def _extract_with_ocr(self, pdf_file) -> str:
        """Extract text from scanned PDF using OCR"""
        try:
            import fitz
            from PIL import Image

            # Check if pytesseract is available
            try:
                import pytesseract
            except ImportError:
                raise Exception("OCR libraries (pytesseract, PIL) not installed")

            # Reset file pointer
            if hasattr(pdf_file, 'seek'):
                pdf_file.seek(0)

            doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
            text_content = []

            # Process first few pages for OCR (can be expensive)
            max_ocr_pages = min(10, doc.page_count)  # Limit OCR to first 10 pages

            for page_num in range(max_ocr_pages):
                try:
                    page = doc.load_page(page_num)

                    # Convert page to image
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x scaling for better OCR
                    img_data = pix.tobytes("png")

                    # Convert to PIL Image
                    img = Image.open(io.BytesIO(img_data))

                    # Perform OCR
                    page_text = pytesseract.image_to_string(img, lang='eng')

                    if page_text and page_text.strip():
                        text_content.append(f"[Page {page_num + 1}]\n{page_text}")

                except Exception as e:
                    logger.warning(f"OCR failed for page {page_num + 1}: {e}")
                    continue

            doc.close()

            if text_content:
                return '\n\n'.join(text_content)
            else:
                raise Exception("OCR produced no readable text")

        except ImportError as e:
            logger.warning(f"OCR libraries not available: {e}")
            raise Exception("OCR libraries (pytesseract, PIL) not installed")
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            raise Exception(f"OCR processing failed: {str(e)}")

    def _post_process_pdf_text(self, text: str) -> str:
        """Enhanced cleaning and normalization for PDF text with academic content preservation"""
        if not text:
            return ""

        logger.info(f"Starting PDF text post-processing on {len(text)} characters")

        # Step 1: Fix broken words and lines
        text = self._fix_text_extraction_artifacts(text)

        # Step 2: Normalize whitespace while preserving structure
        text = self._normalize_whitespace(text)

        # Step 3: Handle academic content specific issues
        text = self._clean_academic_content(text)

        # Step 4: Apply enhanced text cleaning
        text = self._enhanced_text_cleaning(text)

        # Step 5: Validate and ensure quality
        text = self._validate_and_finalize(text)

        logger.info(f"PDF post-processing complete. Final length: {len(text)} characters")
        return text

    def _fix_text_extraction_artifacts(self, text: str) -> str:
        """Fix common PDF text extraction issues"""
        # Fix hyphenated words broken across lines
        text = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', text)

        # Fix words broken across lines (but not proper nouns or section headers)
        text = re.sub(r'(\w)\s*\n\s*(?![A-Z])', r'\1 ', text)

        # Fix broken sentences at line endings
        text = re.sub(r'([.!?])\s*\n\s*([A-Z])', r'\1\n\2', text)

        # Fix missing spaces after periods in common abbreviations
        text = re.sub(r'(\w)\.([A-Z])', r'\1. \2', text)

        return text

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace while preserving document structure"""
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)

        # Normalize paragraph breaks (preserve intentional double newlines)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

        # Fix spacing around punctuation
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        text = re.sub(r'([.,!?;:])\s+', r'\1 ', text)

        # Remove trailing/leading whitespace on lines
        lines = text.split('\n')
        lines = [line.strip() for line in lines if line.strip()]
        text = '\n'.join(lines)

        return text

    def _clean_academic_content(self, text: str) -> str:
        """Clean academic-specific content while preserving important information"""
        # Remove page numbers (but not chapter/section numbers)
        text = re.sub(r'^\s*-?\s*\d+\s*$', '', text, flags=re.MULTILINE)

        # Remove common headers/footers but preserve section content
        text = re.sub(r'^.*?(?=Abstract|Introduction|Chapter|Section|Conclusion)',
                     '', text, flags=re.MULTILINE | re.IGNORECASE)

        # Clean citation markers but preserve the sentence structure
        text = re.sub(r'\s*\[\d+\]', '', text)  # Remove [1], [2], etc.
        text = re.sub(r'\s*\(\d{4}\)', '', text)  # Remove (2023)

        # Remove figure/table captions but preserve context
        text = re.sub(r'(?:Figure|Fig\.|Table|TABLE)\s*\d+[:.]?\s*.*?(?=\n\n|$)',
                     '', text, flags=re.IGNORECASE | re.DOTALL)

        # Clean up excessive bullet points or numbering
        text = re.sub(r'^\s*[\d]+\.?\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*[•●■]\s*', '', text, flags=re.MULTILINE)

        return text

    def _enhanced_text_cleaning(self, text: str) -> str:
        """Apply enhanced text cleaning while preserving academic integrity"""
        # Use the existing clean_text function but with PDF-specific enhancements
        text = clean_text(text)

        # Additional cleaning for academic content
        # Remove isolated numbers that are likely page remnants
        text = re.sub(r'(?<!\w)\d+(?!\w)', '', text)

        # Fix common OCR-like errors in academic text
        text = re.sub(r'\b(\w+)l\b', r'\1I', text)  # l -> I
        text = re.sub(r'\b(\w+)0\b', r'\1O', text)  # 0 -> O

        return text

    def _validate_and_finalize(self, text: str) -> str:
        """Final validation and cleanup"""
        if not text or len(text.strip()) < 50:
            raise Exception("Insufficient text content after processing")

        # Ensure text starts with proper capitalization
        sentences = text.split('. ')
        if sentences and sentences[0]:
            sentences[0] = sentences[0][0].upper() + sentences[0][1:] if sentences[0] else sentences[0]

        text = '. '.join(sentences)

        # Final whitespace normalization
        text = ' '.join(text.split())

        return text

    def get_pdf_metadata(self, pdf_file) -> Dict[str, Any]:
        """Extract comprehensive metadata from PDF with enhanced error handling"""
        logger.info("Extracting PDF metadata...")

        metadata = {
            'title': 'Unknown',
            'author': 'Unknown',
            'pages': 'Unknown',
            'size': 'Unknown',
            'creation_date': 'Unknown',
            'producer': 'Unknown',
            'subject': 'Unknown',
            'keywords': 'Unknown',
            'is_encrypted': False,
            'has_text': False,
            'language': 'Unknown'
        }

        try:
            # Reset file pointer if needed
            if hasattr(pdf_file, 'seek'):
                pdf_file.seek(0)

            # Try PyMuPDF first for better metadata
            if self.use_pymupdf:
                try:
                    import fitz
                    if hasattr(pdf_file, 'seek'):
                        pdf_file.seek(0)
                    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")

                    pdf_metadata = doc.metadata
                    metadata.update({
                        'title': pdf_metadata.get('title', 'Unknown') or 'Unknown',
                        'author': pdf_metadata.get('author', 'Unknown') or 'Unknown',
                        'creation_date': pdf_metadata.get('creationDate', 'Unknown'),
                        'producer': pdf_metadata.get('producer', 'Unknown'),
                        'subject': pdf_metadata.get('subject', 'Unknown'),
                        'keywords': pdf_metadata.get('keywords', 'Unknown'),
                        'pages': doc.page_count,
                        'is_encrypted': doc.is_encrypted,
                        'language': self._detect_language(pdf_metadata)
                    })

                    # Check if PDF has extractable text
                    metadata['has_text'] = self._check_text_content(doc)

                    doc.close()
                    logger.info("Successfully extracted metadata using PyMuPDF")

                except ImportError:
                    logger.warning("PyMuPDF not available for metadata extraction")
                except Exception as e:
                    logger.warning(f"PyMuPDF metadata extraction failed: {e}")

            # Fallback to PyPDF2
            if metadata['pages'] == 'Unknown':
                try:
                    if hasattr(pdf_file, 'seek'):
                        pdf_file.seek(0)
                    pdf_reader = PyPDF2.PdfReader(pdf_file)

                    pdf_metadata = pdf_reader.metadata
                    metadata.update({
                        'title': pdf_metadata.get('/Title', 'Unknown') or 'Unknown',
                        'author': pdf_metadata.get('/Author', 'Unknown') or 'Unknown',
                        'pages': len(pdf_reader.pages),
                        'is_encrypted': pdf_reader.is_encrypted,
                    })

                    logger.info("Extracted metadata using PyPDF2 fallback")

                except Exception as e:
                    logger.error(f"PyPDF2 metadata extraction failed: {e}")

            # Get file size
            if hasattr(pdf_file, 'seek') and hasattr(pdf_file, 'tell'):
                current_pos = pdf_file.tell()
                pdf_file.seek(0, 2)  # Seek to end
                metadata['size'] = pdf_file.tell()
                pdf_file.seek(current_pos)  # Return to original position
            else:
                metadata['size'] = 'Unknown'

            logger.info(f"PDF metadata extraction complete: {metadata['pages']} pages, {metadata['title']}")
            return metadata

        except Exception as e:
            logger.error(f"Error extracting PDF metadata: {e}")
            return metadata

    def _detect_language(self, metadata: Dict) -> str:
        """Detect document language from metadata"""
        # Check if language is explicitly specified
        if 'language' in metadata and metadata['language']:
            return metadata['language']

        # Try to infer from producer or other fields
        producer = metadata.get('producer', '').lower()
        if 'adobe' in producer:
            return 'English'  # Default assumption

        return 'Unknown'

    def _check_text_content(self, doc) -> bool:
        """Check if PDF contains extractable text content"""
        try:
            # Try to extract text from first few pages
            for i in range(min(3, doc.page_count)):
                page = doc.load_page(i)
                text = page.get_text("text").strip()
                if len(text) > 100:  # Substantial text found
                    return True
            return False
        except:
            return False

    def validate_pdf(self, pdf_file) -> tuple[bool, str]:
        """Comprehensive PDF validation with detailed error reporting"""
        logger.info("Starting PDF validation...")

        try:
            # Step 1: Check file extension
            if hasattr(pdf_file, 'filename'):
                filename = pdf_file.filename.lower()
                if not filename.endswith('.pdf'):
                    return False, "File must have .pdf extension"

            # Step 2: Check file size (basic validation)
            if hasattr(pdf_file, 'seek') and hasattr(pdf_file, 'tell'):
                current_pos = pdf_file.tell()
                pdf_file.seek(0, 2)  # Seek to end
                file_size = pdf_file.tell()
                pdf_file.seek(current_pos)  # Return to original position

                if file_size == 0:
                    return False, "PDF file appears to be empty"
                elif file_size > 50 * 1024 * 1024:  # 50MB limit
                    return False, "PDF file is too large (max 50MB)"

            # Step 3: Try to read PDF structure
            try:
                if hasattr(pdf_file, 'seek'):
                    pdf_file.seek(0)

                # Try PyMuPDF first
                if self.use_pymupdf:
                    try:
                        import fitz
                        if hasattr(pdf_file, 'seek'):
                            pdf_file.seek(0)
                        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")

                        if doc.page_count == 0:
                            doc.close()
                            return False, "PDF contains no pages"

                        # Check if PDF is encrypted
                        if doc.is_encrypted:
                            doc.close()
                            return False, "PDF is password-protected"

                        doc.close()
                        return True, f"Valid PDF with {doc.page_count} pages"

                    except ImportError:
                        pass
                    except Exception as e:
                        logger.warning(f"PyMuPDF validation failed: {e}")

                # Fallback to PyPDF2
                if hasattr(pdf_file, 'seek'):
                    pdf_file.seek(0)
                pdf_reader = PyPDF2.PdfReader(pdf_file)

                if len(pdf_reader.pages) == 0:
                    return False, "PDF contains no pages"

                if pdf_reader.is_encrypted:
                    return False, "PDF is password-protected"

                return True, f"Valid PDF with {len(pdf_reader.pages)} pages"

            except PyPDF2.errors.PdfReadError as e:
                return False, f"PDF file is corrupted or invalid: {str(e)}"
            except UnicodeDecodeError:
                return False, "PDF file contains invalid characters"
            except PermissionError:
                return False, "Cannot access PDF file (permission denied)"
            except Exception as e:
                return False, f"Error reading PDF: {str(e)}"

        except Exception as e:
            logger.error(f"Unexpected error during PDF validation: {e}")
            return False, f"Validation failed: {str(e)}"

    def diagnose_pdf_issues(self, pdf_file) -> Dict[str, Any]:
        """Provide detailed diagnosis of PDF issues"""
        diagnosis = {
            'is_valid': False,
            'issues': [],
            'recommendations': [],
            'metadata': {}
        }

        # Check file extension
        if hasattr(pdf_file, 'filename'):
            filename = pdf_file.filename.lower()
            if not filename.endswith('.pdf'):
                diagnosis['issues'].append("File extension is not .pdf")
                diagnosis['recommendations'].append("Ensure file has .pdf extension")

        # Check file size
        try:
            if hasattr(pdf_file, 'seek') and hasattr(pdf_file, 'tell'):
                current_pos = pdf_file.tell()
                pdf_file.seek(0, 2)
                file_size = pdf_file.tell()
                pdf_file.seek(current_pos)

                if file_size == 0:
                    diagnosis['issues'].append("File is empty")
                    diagnosis['recommendations'].append("Check if file was properly saved")
                elif file_size > 50 * 1024 * 1024:
                    diagnosis['issues'].append("File is too large (>50MB)")
                    diagnosis['recommendations'].append("Reduce file size or split into smaller PDFs")
        except:
            diagnosis['issues'].append("Cannot determine file size")

        # Try to extract metadata for more info
        try:
            metadata = self.get_pdf_metadata(pdf_file)
            diagnosis['metadata'] = metadata

            if metadata['pages'] == 'Unknown' or metadata['pages'] == 0:
                diagnosis['issues'].append("Cannot read PDF structure")
                diagnosis['recommendations'].append("PDF may be corrupted or use unsupported format")

        except Exception as e:
            diagnosis['issues'].append(f"Metadata extraction failed: {str(e)}")

        diagnosis['is_valid'] = len(diagnosis['issues']) == 0
        return diagnosis