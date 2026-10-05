# Holdit Micro-Architecture

HoldIt is a modern, modular geospatial inventory reservation system.

## High-Level Architecture
- **Frontend**: Next.js 14, React 18, Tailwind CSS, providing a responsive UI.
- **Backend**: FastAPI (Python), serving RESTful endpoints for authentication, reservations, and inventory management.
- **Database**: PostgreSQL with PostGIS extension for handling geospatial queries (like finding stores near a user's location).

## Data Flow
1. **User Request**: User opens frontend, requests nearby stores.
2. **Backend API**: The FastAPI backend routes the request to `StoreService`.
3. **Database Query**: `StoreService` queries Postgres/PostGIS using `ST_DWithin` to find stores matching the geospatial criteria.
4. **Reservation**: User reserves a product. A reservation is created with a 10-minute expiry (managed via background sweeper tasks in `main.py`).

## Core Components
- `backend/app/api/routes`: Contains FastAPI route definitions.
- `backend/app/services`: Contains business logic (Inventory, Reservation, Payment).
- `backend/app/models`: SQLAlchemy ORM models mapped to Postgres tables.
- `backend/app/schemas`: Pydantic models for request validation and response formatting.
- `backend/main.py`: Entry point for FastAPI, configured with background lifecycle tasks (replacing legacy Celery).
- `frontend/app`: Next.js App Router structure.
- `frontend/components`: Reusable UI components.
- `frontend/lib`: API client and configuration utilities.

## Deployment Model
The application is designed to be fully containerized. A `docker-compose.yml` file is provided that spins up:
- PostgreSQL + PostGIS container
- FastAPI Backend container
- Next.js Frontend container

All services communicate over the internal Docker network, ensuring a seamless and reliable end-to-end setup.
