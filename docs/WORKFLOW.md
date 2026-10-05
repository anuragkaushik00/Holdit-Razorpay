# Holdit End-to-End Workflow

## 1. Environment Setup (Automated)
The system is configured with safe mock defaults. By default, developers do not need to configure `.env` files.
- `POSTGRES_URL` defaults to a local connection string.
- `NEXT_PUBLIC_API_URL` defaults to `http://localhost:8000`.

## 2. Bootstrapping
When `docker-compose up` is executed:
- The PostgreSQL/PostGIS container boots up and creates the `holdit` database.
- The FastAPI Backend boots up and automatically connects to the database.
- The Next.js Frontend boots up and points its API client to the backend.

## 3. User Flows
### Authentication
- User navigates to the frontend `/login` or `/register` route.
- A request is sent to `/auth/login` or `/auth/register`.
- The backend validates the request, generates a JWT, and returns it.
- Frontend stores the JWT in `localStorage` and redirects to the dashboard.

### Store and Product Discovery
- The dashboard calls `/stores` and `/products`.
- Backend uses PostGIS queries to find geographically near stores and their inventory.
- The frontend renders stores on a map and lists available products.

### Reserving an Item
- User selects a product at a store and clicks "Reserve".
- A POST request is sent to `/reservations`.
- The backend checks `StoreInventory`, decrements the count by 1, and creates a `Reservation` with status `PENDING` and a 10-minute expiry.
- A 6-digit OTP is generated and returned to the user.

### Payment and Confirmation
- The user can opt to pay via Razorpay (mocked or real).
- Once paid, the backend verifies the Razorpay signature and updates the reservation to `CONFIRMED`.

### Automatic Expiry (Sweeper Task)
- The backend `main.py` runs a background task every minute.
- Any `PENDING` reservations older than 10 minutes that haven't been paid for are marked `EXPIRED`.
- The `StoreInventory` count is incremented back by 1.
