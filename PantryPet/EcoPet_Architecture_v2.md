# System Architecture & Technical Blueprint: "EcoPet" (v2.0)

**Prepared by:** Aung Ko Ko  
**Document Version:** 2.0  
**Focus Areas:** React Frontend, FastAPI Backend, Computer Vision, Subscription Integration

---

## 1. High-Level System Architecture (Updated Stack)

### 1.1. Frontend (React)
* **Framework:** React.js (or React Native for mobile/cross-platform).
* **State Management:** Redux Toolkit or React Query for handling the asynchronous data fetching (inventory updates, pet status) from the FastAPI backend.
* **Subscription UI:** A dedicated Premium portal utilizing Stripe Elements (or local payment gateways) to handle ad-free upgrades.

### 1.2. Backend (FastAPI)
* **Framework:** FastAPI (Python). This provides incredibly fast performance through asynchronous endpoints and automatic interactive API documentation (Swagger UI).
* **AI Integration:** Because FastAPI is a Python framework, it natively and seamlessly integrates with your object detection models (YOLOv8, OpenCV) without needing complex microservice communication for standard workloads.
* **Authentication:** OAuth2 with JWT (JSON Web Tokens) to secure user sessions and subscription validation.

---

## 2. Core Logic Updates

### 2.1. Handling Multiple Quantities & Varying Shelf Lives (Batching Logic)
To handle scenarios where a user has 2 apples expiring in 3 days and 3 apples expiring in 7 days, we use a **Batch Inventory System**.
* **The Logic:** We do *not* aggregate ingredients by name. Instead, every time a user logs an upload, it creates a unique "Batch" row in the database.
* **Consumption (FIFO - First In, First Out):** When the user cooks a recipe requiring "2 Apples", the backend queries the database for apples ordered by `expiry_date ASC`. It deducts the quantity from the batch expiring soonest. If that batch hits 0, it deducts the remainder from the next batch.

### 2.2. Subscription System (Ad-Free Experience)
* **Freemium Model:** Free users receive ads (e.g., via Google AdMob in React Native) and are subject to the 3-recipes-per-day limit.
* **Premium Tier:** Removes ads and potentially unlocks unlimited recipe generation or exclusive digital pet skins.
* **Backend Check:** FastAPI uses dependency injection (`Depends(get_current_user)`) on relevant routes to check the `subscription_tier` before serving ads or enforcing rate limits.

---

## 3. Updated SQL Database Schema (PostgreSQL)

### Table: `Users`
* `user_id` (UUID, Primary Key)
* `username` (VARCHAR)
* `recipes_generated_today` (INT)
* `subscription_tier` (ENUM: 'Free', 'Premium') -> *New*
* `subscription_expiry` (TIMESTAMP, Nullable) -> *New*

### Table: `Subscriptions_Log` *(New)*
* `transaction_id` (UUID, Primary Key)
* `user_id` (UUID, Foreign Key)
* `payment_date` (TIMESTAMP)
* `amount` (DECIMAL) -> *Can be tracked in RM or USD*
* `status` (ENUM: 'Success', 'Failed', 'Refunded')

### Table: `Ingredients_Inventory` *(Updated for Batches)*
* `batch_id` (UUID, Primary Key) -> *Renamed from item_id for clarity*
* `user_id` (UUID, Foreign Key)
* `item_name` (VARCHAR)
* `quantity` (DECIMAL) -> *New: Allows tracking specific amounts (e.g., 2.5)*
* `unit` (VARCHAR) -> *New: 'kg', 'pieces', 'liters'*
* `upload_date` (TIMESTAMP)
* `expiry_date` (TIMESTAMP)
* `status` (ENUM: 'Pantry', 'Consumed', 'Expired', 'Discarded')

### Table: `Digital_Pet`
* `pet_id` (UUID, Primary Key)
* `user_id` (UUID, Foreign Key)
* `health_points` (INT)
* `mood_status` (VARCHAR)
* `appearance_level` (INT)
---

## 4. API Endpoint Strategy (FastAPI)

* `POST /inventory/upload/` -> Accepts the image, runs the Python CV model, returns detected ingredients with suggested shelf life.
* `POST /inventory/confirm/` -> User confirms the quantities and units. Creates new batch rows in `Ingredients_Inventory`.
* `POST /recipes/generate/` -> Checks `user.subscription_tier`. If 'Free' and count > 3, returns 403 Forbidden. Otherwise, fetches closest-to-expiry ingredients and calls Spoonacular API.
* `POST /payments/subscribe/` -> Webhook endpoint for the payment gateway to update the user's `subscription_tier` to 'Premium'.
