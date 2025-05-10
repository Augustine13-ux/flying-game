import re
from typing import Optional
import google.generativeai as genai
from pathlib import Path
import pytesseract
from pdf2image import convert_from_path
import io

class RenamerService:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-pro")
        
    def _extract_text_from_pdf(self, pdf_path: Path, max_chars: int = 500) -> str:
        """Extract text from PDF, using OCR if no text layer exists."""
        try:
            # First try direct text extraction
            import PyPDF2
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                    if len(text) >= max_chars:
                        break
                if text.strip():
                    return text[:max_chars]
            
            # If no text found, use OCR
            images = convert_from_path(pdf_path)
            text = ""
            for image in images:
                text += pytesseract.image_to_string(image)
                if len(text) >= max_chars:
                    break
            return text[:max_chars]
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {str(e)}")

    def _clean_filename(self, filename: str) -> str:
        """Clean filename by removing forbidden characters and ensuring snake_case."""
        # Remove forbidden filesystem characters
        cleaned = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Convert to snake_case
        cleaned = re.sub(r'[^a-zA-Z0-9]', '_', cleaned)
        # Remove multiple underscores
        cleaned = re.sub(r'_+', '_', cleaned)
        # Remove leading/trailing underscores
        cleaned = cleaned.strip('_')
        return cleaned

    def _generate_filename_with_gemini(self, text: str) -> Optional[str]:
        """Generate filename using Gemini AI."""
        prompt = """You are an expert paralegal. Suggest a concise snake_case filename 
        (max 60 chars) using YYYY-MM-DD + short descriptive title."""
        
        try:
            response = self.model.generate_content(
                prompt + "\n\nDocument text:\n" + text,
                generation_config={"temperature": 0.2}
            )
            return self._clean_filename(response.text)
        except Exception:
            return None

    def _fallback_filename(self, text: str) -> str:
        """Generate fallback filename using regex pattern."""
        # Try to find a date in YYYY-MM-DD format
        date_match = re.search(r'\d{4}-\d{2}-\d{2}', text)
        date = date_match.group(0) if date_match else "unknown-date"
        
        # Extract first few words as title
        words = re.findall(r'\b\w+\b', text)[:5]
        title = '_'.join(words).lower()
        
        return f"{date}_{title}"

    def suggest_filename(self, pdf_path: Path) -> str:
        """Generate a suggested filename for the PDF."""
        text = self._extract_text_from_pdf(pdf_path)
        
        # Try Gemini first
        suggested_name = self._generate_filename_with_gemini(text)
        if suggested_name and len(suggested_name) <= 60:
            return suggested_name
            
        # Fallback to regex-based approach
        return self._fallback_filename(text) 