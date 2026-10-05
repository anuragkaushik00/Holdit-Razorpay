# Holdit API Documentation

All responses conform to a unified standard format:
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional descriptive message"
}
```

## Authentication `/auth`
- `POST /auth/register`: Register a new user (CUSTOMER, STORE_STAFF, ADMIN).
- `POST /auth/login`: Authenticate and receive an access/refresh token pair.
- `POST /auth/refresh`: Refresh an expired access token using a valid refresh token.

## Stores `/stores`
- `GET /stores`: List all stores. (Supports geospatial query parameters).
- `GET /stores/{store_id}`: Retrieve a specific store's details.

## Products & Inventory `/products` & `/inventory`
- `GET /products`: List all global products in the system.
- `GET /inventory/{store_id}`: Get available product inventory for a specific store.

## Reservations `/reservations`
- `POST /reservations`: Create a new inventory hold/reservation. Returns a 6-digit OTP.
- `GET /reservations`: List the current user's reservations.
- `GET /reservations/{reservation_id}`: Details for a specific reservation.
- `POST /reservations/{reservation_id}/cancel`: Cancel a pending reservation and release the hold.

## Payments `/payments`
- `POST /payments/create-order`: Generates a Razorpay order ID for a specific reservation.
- `POST /payments/verify`: Verifies the Razorpay signature and confirms the reservation.
