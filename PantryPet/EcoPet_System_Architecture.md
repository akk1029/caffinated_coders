# System Architecture & Technical Blueprint: "EcoPet" (Digital Pet & Food Waste Tracker)

**Prepared by:** Aung Ko Ko  
**Document Version:** 1.0  
**Focus Areas:** Computer Vision, Data Science, System Architecture, API Integrations  

---

## 1. Executive Summary
This document outlines the complete system architecture, database schema, API strategy, and implementation roadmap for a mobile application centered around reducing food waste. The core differentiator is a gamified "Digital Pet" (Tamagotchi-style) whose mood, appearance, and survival depend directly on the user's food consumption and waste habits. The system integrates computer vision for ingredient detection, external datasets for shelf-life tracking, and recipe generation APIs to minimize spoilage.

---

## 2. High-Level System Architecture

The architecture follows a modern, scalable microservices-inspired approach, separating the client interface from the core backend and the heavy artificial intelligence processing.

### 2.1. Frontend (Mobile App)
* **Framework:** Flutter or React Native (Cross-platform support for iOS & Android).
* **State Management:** Riverpod (Flutter) or Redux (React Native) to handle the complex state of the digital pet's mood and the inventory of ingredients.
* **Local Storage:** SQLite (via mobile plugins) to cache the pet's state and recent ingredients for offline viewing.

### 2.2. Backend (Core API)
* **Framework:** Python (FastAPI or Django REST Framework). Python is chosen for its seamless integration with data science libraries and ML models.
* **Hosting:** AWS EC2 or Google Cloud Run.
* **Background Tasks:** Celery + Redis for asynchronous tasks (e.g., daily cron jobs to update ingredient expiry, decay pet health, and calculate leaderboard rankings).

### 2.3. AI & Computer Vision Microservice
* **Stack:** Python, OpenCV, PyTorch/YOLOv8.
* **Functionality:** Handles the object detection pipeline. When a user uploads an image, this service processes the image, identifies the ingredients (e.g., Apple, Onion, Chicken), and returns the bounding boxes and confidence scores to the backend.

### 2.4. External APIs & Datasets
* **Shelf Life Data:** * *Option A (Dataset):* FoodKeeper Dataset (provided by USDA). Highly reliable CSV/JSON dataset that can be imported directly into the SQL database to avoid API rate limits.
    * *Option B (API):* Open Food Facts API (useful for barcode scanning if added later).
* **Recipe Generation API:** Spoonacular API or Edamam API. Both support "search by ingredients" endpoints.

---

## 3. Core Modules & Logic Workflows

### 3.1. Ingredient Logging & Object Detection
1.  **Image Capture:** User takes a photo.
2.  **Inference:** Image sent to the CV Microservice. YOLO object detection model identifies items.
3.  **Validation:** User confirms the detected items (e.g., "Did you mean 3 Tomatoes?").
4.  **Expiry Calculation:** Backend queries the FoodKeeper dataset to find the standard shelf life (e.g., Tomatoes = 7 days). Expiry Date = Upload Date + 7 days.

### 3.2. Digital Pet (Tamagotchi) Engine
The pet's state is evaluated daily via a Celery background job at 00:00 server time.
* **Health Points (HP):** Maximum 100.
* **Mood States:** Happy, Neutral, Sad, Sick, Dying.
* **Logic Engine:**
    * *Positive Actions:* Logging food (+HP), using food before expiry (+HP), generating and cooking a recipe (+HP).
    * *Negative Actions:* Food reaching its expiration date without being consumed (-HP), throwing away food (-HP).
* **Visuals:** The app fetches different sprite assets or Lottie animations based on the calculated mood state.

### 3.3. Recipe Generation (Expiring Soon)
* **Trigger:** User requests a recipe.
* **Filter:** Backend queries the SQL database for ingredients belonging to the user where `expiry_date <= CURRENT_DATE + 3`.
* **API Call:** Backend formats these ingredients into a comma-separated string and calls the Spoonacular API.
* **Rate Limiting Check:** Ensure the `recipes_generated_today` count for the user is `< 3`.

### 3.4. Impact Dashboard & Leaderboard
* **Metrics:** * **Financial:** Estimated money saved (displayed in RM) based on average market price datasets multiplied by consumed ingredients.
    * **Environmental:** CO2 saved (kg). (Formula: Weight of consumed food * average carbon footprint of food waste, approx 2.5kg CO2 per 1kg of food waste).
* **Leaderboard:** Ranks users globally or locally based on the "Pet Level" or total CO2 saved.

---

## 4. SQL Database Schema (PostgreSQL)

A relational database is perfect for structured user, inventory, and relational API data.

### Table: `Users`
* `user_id` (UUID, Primary Key)
* `username` (VARCHAR)
* `recipes_generated_today` (INT, resets daily)
* `total_co2_saved` (DECIMAL)
* `total_money_saved` (DECIMAL)

### Table: `Digital_Pet`
* `pet_id` (UUID, Primary Key)
* `user_id` (UUID, Foreign Key)
* `health_points` (INT)
* `mood_status` (VARCHAR)
* `appearance_level` (INT)

### Table: `Ingredients_Inventory`
* `item_id` (UUID, Primary Key)
* `user_id` (UUID, Foreign Key)
* `item_name` (VARCHAR)
* `upload_date` (TIMESTAMP)
* `expiry_date` (TIMESTAMP)
* `status` (ENUM: 'Pantry', 'Consumed', 'Expired', 'Discarded')
* `estimated_cost` (DECIMAL) - *Used to calculate RM saved.*

### Table: `Reference_Shelf_Life` (Populated from Dataset)
* `ingredient_name` (VARCHAR, Primary Key)
* `category` (VARCHAR)
* `pantry_days` (INT)
* `fridge_days` (INT)

---

## 5. API Limitations & Mitigation Strategies

1.  **Recipe API Quotas (Spoonacular):**
    * *Limitation:* Free tiers often limit daily requests (e.g., 150 points/day).
    * *Mitigation:* The hard limit of "3 recipes per user per day" is excellent. Additionally, implement **Redis Caching**. If User A searches for "Chicken, Rice, Onion", cache the API response for 24 hours. If User B searches the same combination, serve from Redis instead of pinging the external API.
2.  **Object Detection Latency:**
    * *Limitation:* Running heavy CV models on the backend can cause timeout errors on the mobile client.
    * *Mitigation:* Optimize the model (e.g., export to ONNX or TensorRT). Compress the image on the mobile device before sending it over the network.
3.  **Cron Job Scalability:**
    * *Limitation:* Updating thousands of pets at exactly midnight will lock the database.
    * *Mitigation:* Batch processing. Process users in chunks of 500, or stagger the pet updates based on the user's local timezone.

---

## 6. Development Roadmap

* **Phase 1: Data Preparation & ML**
    * Gather and clean the FoodKeeper dataset.
    * Train/Fine-tune the object detection model on common pantry items.
* **Phase 2: Backend & Database Integration**
    * Set up PostgreSQL and build out the Django/FastAPI endpoints.
    * Implement the Tamagotchi state logic and Celery cron jobs.
* **Phase 3: Client App Development**
    * Build Flutter UI.
    * Integrate camera functionality and API connections.
    * Design and implement pet animations.
* **Phase 4: Dashboard & Gamification**
    * Calculate CO2 and monetary conversions (RM).
    * Deploy leaderboard endpoints.
