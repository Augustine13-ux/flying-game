import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from pathlib import Path
from app.main import app

client = TestClient(app)

@patch('app.services.renamer.RenamerService')
def test_get_rename_suggestions(mock_renamer, tmp_path):
    # Setup mock PDF files
    job_dir = tmp_path / "test-job"
    job_dir.mkdir()
    (job_dir / "doc1.pdf").write_text("")
    (job_dir / "doc2.pdf").write_text("")
    
    # Mock renamer service
    mock_instance = MagicMock()
    mock_instance.suggest_filename.side_effect = [
        "2024-03-20_legal_document_1",
        "2024-03-20_legal_document_2"
    ]
    mock_renamer.return_value = mock_instance
    
    # Mock settings
    with patch('app.api.endpoints.jobs.settings') as mock_settings:
        mock_settings.UPLOAD_DIR = str(tmp_path)
        mock_settings.GOOGLE_API_KEY = "dummy-key"
        
        # Make request
        response = client.get("/api/job/test-job/rename-suggestions")
        
        # Assert response
        assert response.status_code == 200
        assert response.json() == {
            "suggestions": {
                "doc1.pdf": "2024-03-20_legal_document_1",
                "doc2.pdf": "2024-03-20_legal_document_2"
            }
        }

def test_get_rename_suggestions_job_not_found():
    response = client.get("/api/job/nonexistent-job/rename-suggestions")
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found" 