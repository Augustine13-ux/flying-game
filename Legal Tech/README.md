# Signature Toolkit

A modern full-stack application for signature extraction and processing.

## Tech Stack

- Backend: Python 3.12 + FastAPI
- Frontend: Next.js 14 + TypeScript + Tailwind CSS
- Development: Docker Compose with hot-reload
- Quality: Pre-commit hooks (ruff + black) and GitHub Actions

## Development Setup

1. Install Docker and Docker Compose
2. Clone this repository
3. Run the application:
   ```bash
   docker compose up
   ```

The services will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Development Tools

### Pre-commit Hooks

Install pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```

### Backend Development

The backend uses Poetry for dependency management:
```bash
cd api
poetry install
poetry run uvicorn app.main:app --reload
```

### Frontend Development

The frontend uses npm:
```bash
cd web
npm install
npm run dev
```

## Testing

Run backend tests:
```bash
cd api
poetry run pytest
```

Run frontend linting:
```bash
cd web
npm run lint
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests and linting
4. Submit a pull request

## License

MIT 