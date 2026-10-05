# Holdit-Razorpay

HoldIt is a **geospatial inventory reservation system** that helps users reserve products at nearby stores. This project features a Next.js frontend, a FastAPI backend, and Razorpay integration for payments.

## Architecture

- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS
- **Backend**: FastAPI (Python), SQLAlchemy ORM
- **Database**: PostgreSQL with PostGIS for geospatial data
- **Payments**: Razorpay

For detailed architectural information, please see:
- [Micro Architecture](docs/MICRO_ARCHITECTURE.md)
- [Workflow](docs/WORKFLOW.md)
- [API Reference](docs/API.md)

## Quick Start (Docker)

The project has been configured with safe mock default environment variables, so no manual `.env` file configuration is required to get started!

```bash
docker-compose up --build
```

Access the application:
- **Backend API Docs**: http://localhost:8000/docs
- **Frontend App**: http://localhost:3000

## Manual Development Setup

If you prefer running services locally instead of Docker:

### 1. Database
Ensure you have PostgreSQL running with the PostGIS extension enabled on `localhost:5432`.
```sql
CREATE EXTENSION postgis;
```

### 2. Backend
```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --port 8000
```
*Note: A background sweeper task automatically runs every minute to expire stale reservations. Celery and Redis are no longer required for this functionality.*

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```

## Features
- **Geospatial Queries**: Finds nearest stores and availability using PostGIS.
- **Reservations**: 10-minute hold on inventory items.
- **Razorpay**: Integrated payment gateway with secure webhook/HMAC signature verification.
- **Safe Defaults**: Will run out-of-the-box in development.

## Production
In production, ensure you override the safe mock defaults in `.env` files with secure keys, databases, and Razorpay credentials.
