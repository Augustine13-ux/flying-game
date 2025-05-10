import pdfplumber
import re
from pathlib import Path
from typing import List


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