import pdfplumber
import re
from pathlib import Path
from typing import List, Dict
import PyPDF2
import os


class SignatureDetector:
    """Detects pages containing signatures in PDF documents."""

    def __init__(self):
        # Compile regex patterns for better performance
        self.signature_patterns = [
            re.compile(r"Signature", re.IGNORECASE),
            re.compile(r"Signed by", re.IGNORECASE),
            re.compile(r"_{40,}"),  # 40 or more underscores
        ]

    def detect_pages(self, pdf_path: str | Path) -> List[int]:
        """
        Detect pages containing signatures in a PDF document.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of 1-based page indices containing signatures
        """
        signature_pages = []
        
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                
                # Check for signature patterns
                if any(pattern.search(text) for pattern in self.signature_patterns):
                    signature_pages.append(page_num)
            
            # If no signatures found, add the last page
            if not signature_pages and total_pages > 0:
                signature_pages.append(total_pages)
        
        return signature_pages

    def extract_pages(self, pdf_path: str | Path, out_dir: str | Path) -> Dict[int, Dict[str, str]]:
        """
        Extract pages containing signatures and generate PNG images.
        
        Args:
            pdf_path: Path to the PDF file
            out_dir: Directory to save extracted pages and images
            
        Returns:
            Dictionary mapping page numbers to their PDF and PNG file paths
        """
        pdf_path = Path(pdf_path)
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        
        # Get pages with signatures
        signature_pages = self.detect_pages(pdf_path)
        if not signature_pages:
            return {}
            
        # Create output PDF with signature pages
        basename = pdf_path.stem
        output_pdf = out_dir / f"{basename}_sigpages.pdf"
        
        with PyPDF2.PdfReader(pdf_path) as reader:
            writer = PyPDF2.PdfWriter()
            for page_num in signature_pages:
                writer.add_page(reader.pages[page_num - 1])
            
            with open(output_pdf, "wb") as f:
                writer.write(f)
        
        # Generate PNG images and build manifest
        manifest = {}
        with pdfplumber.open(pdf_path) as pdf:
            for page_num in signature_pages:
                page = pdf.pages[page_num - 1]
                image = page.to_image(resolution=300)
                png_path = out_dir / f"{basename}_page{page_num}.png"
                image.save(png_path)
                
                manifest[page_num] = {
                    "pdf": str(output_pdf),
                    "png": str(png_path)
                }
        
        return manifest 