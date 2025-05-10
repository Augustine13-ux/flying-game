import pytest
from pathlib import Path
from app.services.signature_detector import SignatureDetector

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "test_data"
TEST_DATA_DIR.mkdir(exist_ok=True)

@pytest.fixture
def detector():
    return SignatureDetector()

@pytest.fixture
def sample_pdf_path():
    # Create a simple PDF with signature text
    pdf_path = TEST_DATA_DIR / "sample.pdf"
    if not pdf_path.exists():
        # Create a simple PDF with signature text
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        
        # Page 1: No signature
        c.drawString(100, 700, "This is a test document")
        c.showPage()
        
        # Page 2: Has signature text
        c.drawString(100, 700, "Signature: _________________")
        c.showPage()
        
        # Page 3: Has signed by text
        c.drawString(100, 700, "Signed by: John Doe")
        c.showPage()
        
        # Page 4: Has underscore line
        c.drawString(100, 700, "________________________________________")
        c.showPage()
        
        # Page 5: No signature
        c.drawString(100, 700, "End of document")
        c.save()
    
    return pdf_path

@pytest.fixture
def empty_pdf_path():
    # Create an empty PDF
    pdf_path = TEST_DATA_DIR / "empty.pdf"
    if not pdf_path.exists():
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        c.drawString(100, 700, "This is an empty document")
        c.save()
    
    return pdf_path

def test_detect_pages_with_signatures(detector, sample_pdf_path):
    """Test detection of pages with various signature patterns."""
    pages = detector.detect_pages(sample_pdf_path)
    
    # Should detect pages 2, 3, and 4 (1-based indices)
    assert set(pages) == {2, 3, 4}
    assert len(pages) == 3

def test_detect_pages_empty_document(detector, empty_pdf_path):
    """Test detection in a document without signatures."""
    pages = detector.detect_pages(empty_pdf_path)
    
    # Should return the last page (page 1)
    assert pages == [1]
    assert len(pages) == 1

def test_detect_pages_invalid_path(detector):
    """Test handling of invalid PDF path."""
    with pytest.raises(Exception):
        detector.detect_pages("nonexistent.pdf") 