# Price Watchdogs

A lightweight web app that monitors SaaS pricing pages, subscription terms, and plan structures, detects meaningful changes, and alerts users before they get surprised by higher bills.

## Tech Stack

- **Backend**: FastAPI (Python) with SQLAlchemy and Alembic
- **Frontend**: Next.js 14+ with TypeScript and Tailwind CSS
- **Database**: PostgreSQL
- **Infrastructure**: Docker Compose for local development

## Project Structure

```
price-watchdogs/
├── backend/          # FastAPI Python backend
│   ├── app/
│   │   ├── api/      # API route handlers
│   │   ├── models/   # SQLAlchemy models
│   │   ├── schemas/  # Pydantic schemas
│   │   └── services/ # Business logic
│   └── alembic/      # Database migrations
├── frontend/         # Next.js TypeScript frontend
│   ├── app/          # Next.js App Router
│   ├── components/   # React components
│   └── lib/          # Utilities and API clients
└── docker-compose.yml # Local PostgreSQL setup
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- PostgreSQL (via Docker)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file:
```bash
cp .env.example .env
```

5. Update `.env` with your database URL and secret key.

6. Start PostgreSQL with Docker Compose:
```bash
docker-compose up -d
```

7. Run migrations:
```bash
alembic upgrade head
```

8. Start the development server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env.local` file:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

4. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Database Schema

- **User**: Authentication and user data
- **Service**: Monitored services with URLs and check frequencies
- **Snapshot**: Captured page content and hashes
- **ChangeEvent**: Detected changes with classification
- **Alert**: Sent notifications to users

## Development

### Running Migrations

```bash
cd backend
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for interactive API documentation.

## Deployment

### Render

This project is configured for deployment on Render. See [RENDER_SETUP.md](RENDER_SETUP.md) for detailed deployment instructions.

Quick start:
1. Push your code to a Git repository
2. Create a new Blueprint in Render and connect your repository
3. Render will automatically detect `render.yaml` and set up the web service and PostgreSQL database

The application includes:
- `render.yaml` - Infrastructure as Code configuration
- `backend/start.sh` - Startup script that runs migrations and starts the server
- Automatic database URL conversion for Render's PostgreSQL format

## License

MIT

