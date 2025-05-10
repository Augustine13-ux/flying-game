import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from app.services.renamer import RenamerService

@pytest.fixture
def renamer_service():
    return RenamerService(api_key="dummy-key")

@pytest.fixture
def mock_pdf():
    return Path("test.pdf")

def test_clean_filename():
    service = RenamerService(api_key="dummy-key")
    assert service._clean_filename("Test Document.pdf") == "test_document_pdf"
    assert service._clean_filename("Test: Document/with\\special*chars") == "test_document_with_special_chars"
    assert service._clean_filename("  multiple   spaces  ") == "multiple_spaces"

def test_fallback_filename():
    service = RenamerService(api_key="dummy-key")
    text = "2024-03-20 This is a test document for legal proceedings"
    filename = service._fallback_filename(text)
    assert filename == "2024-03-20_this_is_a_test_document"
    
    # Test with no date
    text = "This is a test document without date"
    filename = service._fallback_filename(text)
    assert filename == "unknown-date_this_is_a_test_document"

@patch('app.services.renamer.genai.GenerativeModel')
def test_gemini_filename_generation(mock_gemini, renamer_service, mock_pdf):
    # Mock Gemini response
    mock_response = MagicMock()
    mock_response.text = "2024-03-20_legal_document_contract_agreement"
    mock_gemini.return_value.generate_content.return_value = mock_response
    
    # Mock PDF text extraction
    with patch.object(renamer_service, '_extract_text_from_pdf', return_value="Sample PDF text"):
        filename = renamer_service.suggest_filename(mock_pdf)
        assert filename == "2024-03-20_legal_document_contract_agreement"
        assert len(filename) <= 60
        assert "_" in filename
        assert not any(char in filename for char in '<>:"/\\|?*')

@patch('app.services.renamer.genai.GenerativeModel')
def test_gemini_fallback_on_error(mock_gemini, renamer_service, mock_pdf):
    # Mock Gemini to raise an exception
    mock_gemini.return_value.generate_content.side_effect = Exception("API Error")
    
    # Mock PDF text extraction
    with patch.object(renamer_service, '_extract_text_from_pdf', return_value="2024-03-20 Sample PDF text"):
        filename = renamer_service.suggest_filename(mock_pdf)
        assert filename == "2024-03-20_sample_pdf_text"
        assert len(filename) <= 60
        assert "_" in filename 