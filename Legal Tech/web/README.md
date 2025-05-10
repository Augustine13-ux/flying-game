# Legal Tech Web Application

A modern web application for handling legal document processing with file upload, processing status tracking, and download capabilities.

## Features

- Drag and drop file upload
- Real-time processing status updates
- Thumbnail preview of processed files
- ZIP download of processed files

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

The application will be available at http://localhost:3000

## Development

The application is built with:
- React
- TypeScript
- Tailwind CSS
- React Dropzone
- Axios for API communication

## API Endpoints

The application expects the following API endpoints:

- POST `/api/upload` - Upload files
- GET `/api/job/{job_id}/manifest` - Get processing status
- GET `/api/download/{job_id}` - Download processed files 