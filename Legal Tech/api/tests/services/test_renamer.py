import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.renamer import RenamerService

@pytest.fixture
def mock_gemini():
    with patch('google.generativeai.GenerativeModel') as mock:
        model_instance = MagicMock()
        model_instance.generate_content = AsyncMock()
        mock.return_value = model_instance
        yield mock

@pytest.fixture
def renamer_service():
    return RenamerService(api_key="dummy-key")

@pytest.mark.asyncio
async def test_suggest_filename_with_gemini(renamer_service, tmp_path):
    # Mock PDF text extraction
    with patch('app.services.renamer.RenamerService._extract_text_from_pdf') as mock_extract:
        mock_extract.return_value = "Sample legal document from 2024-03-15 about contract review"
        
        # Patch generate_content on the actual model instance
        mock_response = MagicMock()
        mock_response.text = "2024-03-15_contract_review_document"
        renamer_service.model.generate_content = AsyncMock(return_value=mock_response)
        
        # Test the service
        result = await renamer_service.suggest_filename("dummy.pdf")
        
        # Assertions
        assert result == "2024-03-15_contract_review_document"
        assert len(result) <= 60
        assert "_" in result
        assert result.islower()

@pytest.mark.asyncio
async def test_suggest_filename_fallback(renamer_service, mock_gemini, tmp_path):
    # Mock PDF text extraction
    with patch('app.services.renamer.RenamerService._extract_text_from_pdf') as mock_extract:
        mock_extract.return_value = "Sample legal document from 2024-03-15 about contract review"
        
        # Mock Gemini error
        mock_gemini.return_value.generate_content.side_effect = Exception("API Error")
        
        # Test the service
        result = await renamer_service.suggest_filename("dummy.pdf")
        
        # Assertions
        assert result.startswith("2024-03-15_")
        assert len(result) <= 60
        assert "_" in result
        assert result.islower()

@pytest.mark.asyncio
async def test_clean_filename(renamer_service):
    # Test various filename cleaning scenarios
    test_cases = [
        ("Test Document (2024).pdf", "test_document_2024pdf"),
        ("Contract: Review & Analysis", "contract_review_analysis"),
        ("Legal Doc 2024/03/15", "legal_doc_20240315"),
        ("File with spaces and CAPS", "file_with_spaces_and_caps"),
    ]
    
    for input_name, expected in test_cases:
        result = renamer_service._clean_filename(input_name)
        assert result == expected
        assert len(result) <= 60
        assert "_" in result
        assert result.islower()
        assert not any(c in result for c in '<>:"/\\|?*') 