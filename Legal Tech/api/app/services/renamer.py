import re
from datetime import datetime
from typing import Optional
import google.generativeai as genai
from pdfplumber import open as pdf_open
import pytesseract
from PIL import Image
import io

class RenamerService:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-pro")
        
    def _extract_text_from_pdf(self, pdf_path: str, max_chars: int = 500) -> str:
        """Extract text from PDF, using OCR if no text layer exists."""
        try:
            with pdf_open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                    if len(text) >= max_chars:
                        break
                
                if not text.strip():
                    # No text layer, try OCR on first page
                    first_page = pdf.pages[0]
                    img = first_page.to_image()
                    text = pytesseract.image_to_string(img.original)
                
                return text[:max_chars]
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")

    def _clean_filename(self, filename: str) -> str:
        """Clean filename to be filesystem-safe."""
        # Remove forbidden characters and convert to snake_case
        cleaned = re.sub(r'[<>:"/\\|?*]', '', filename)
        cleaned = re.sub(r'\s+', '_', cleaned)
        cleaned = re.sub(r'[^a-zA-Z0-9_-]', '', cleaned)
        cleaned = re.sub(r'_+', '_', cleaned)  # Collapse multiple underscores
        cleaned = cleaned.strip('_')  # Remove leading/trailing underscores
        return cleaned.lower()

    def _generate_fallback_name(self, text: str) -> str:
        """Generate a fallback filename using regex pattern."""
        # Try to find a date in the text
        date_match = re.search(r'\d{4}[-/]\d{2}[-/]\d{2}', text)
        date_str = date_match.group(0).replace('/', '-') if date_match else datetime.now().strftime('%Y-%m-%d')
        # Extract first few words as title
        words = re.findall(r'\b\w+\b', text)[:5]
        title = '_'.join(words)
        fallback = f"{date_str}_{title}"
        return self._clean_filename(fallback)

    async def suggest_filename(self, pdf_path: str) -> str:
        """Generate a suggested filename for the PDF."""
        try:
            # Extract text from PDF
            text = self._extract_text_from_pdf(pdf_path)
            
            # Build prompt for Gemini
            prompt = f"""You are an expert paralegal. Suggest a concise snake_case filename (max 60 chars) using YYYY-MM-DD + short descriptive title for this document:

{text}

Respond with ONLY the filename, no explanation or additional text."""

            # Get suggestion from Gemini
            response = await self.model.generate_content(
                prompt,
                generation_config={"temperature": 0.2}
            )
            
            # Clean and validate the response
            suggested_name = self._clean_filename(response.text)
            if len(suggested_name) > 60:
                suggested_name = suggested_name[:60]
                
            return suggested_name
            
        except Exception as e:
            # Fallback to regex-based naming
            text = self._extract_text_from_pdf(pdf_path)
            return self._generate_fallback_name(text) 