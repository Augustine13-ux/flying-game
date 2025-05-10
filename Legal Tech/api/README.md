# Signature Toolkit API

A FastAPI backend for extracting and processing signatures from PDF documents.

## Features

- PDF signature page extraction
- OCR text extraction
- AI-powered file renaming
- File upload and management

## Setup

1. Install dependencies:
```bash
poetry install
```

2. Set up environment variables:
```bash
export GOOGLE_API_KEY=your_api_key_here
```

3. Run the development server:
```bash
poetry run uvicorn app.main:app --reload
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc 