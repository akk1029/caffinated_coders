# PantryPet

> Turn cutting food waste into a game — track your pantry, rescue food before it expires, and keep your digital eco-pet thriving.

**ImagineHack 2026 · Track 3 · Team Caffeinated Coders**

---

## Team Caffeinated Coders

1. Aung Ko Ko
2. Joshua Angelo Kana
3. Kaung Khant Thaw
4. Raul Jr. Jalin Manalo

---

## Description

Roughly **a third of all food produced is wasted**, costing households money and pumping avoidable CO₂ into the atmosphere. Most people *want* to waste less, but tracking what's in the fridge is tedious and easy to forget.

**PantryPet** makes it effortless — and fun. It's an installable mobile web app (PWA) that:

- Lets you **log groceries in seconds** by snapping a receipt or photo (AI does the rest), or adding items by hand.
- **Warns you what's about to expire** and suggests **recipes that use those items first**.
- Rewards you with a **digital pet** that grows healthier and evolves every time you rescue food — and gets sad when you let it spoil.
- Shows your real **CO₂ saved** and **money saved (RM)**, and ranks you on a community **leaderboard**.

The result: a Tamagotchi-style nudge that turns a boring chore into a daily habit with measurable environmental impact.

---

##  Features

| Feature | What it does |
|---|---|
| **AI Receipt Scanner** | OCR a grocery receipt  (upload/snap) → auto-extracts items, **RM prices**, and shelf-life expiry, then adds them to your pantry. Works with English receipts; falls back to free OCR so it runs with zero paid setup. |
| **Smart Manual Add** | Type an item — shelf-life expiry (FoodSafety.gov data) and estimated cost are filled in automatically. |
| **Recipe Generator** | Suggests recipes (via TheMealDB) from your pantry, **prioritising items expiring soon**. Save recipes, watch the YouTube guide, and tap **"Cooked"** to auto-remove used ingredients from your pantry. |
| **Digital Eco-Pet** | A pet (fox, wolf, tiger, dragon, or bat) whose health, mood, and evolution stage are driven by how much food you rescue vs. waste. |
| **Impact Dashboard** | Live pantry count, "expiring soon" alerts, total **CO₂ saved** and **money saved**, and pet status. |
| **Leaderboard** | Ranks users by CO₂ saved, with an animated pet podium. |
| **Free & Premium tiers** | Free: 3 recipe generations + 2 receipt scans per day. Premium: unlimited recipes + 10 scans/day. |
| **Installable PWA** | Add to home screen, works like a native app. |

---

## Technologies Used

**Backend**
- **Python · FastAPI** (async REST API + server-rendered pages)
- **PostgreSQL** with **SQLAlchemy 2.0 (async)** + **asyncpg**
- **Redis** — caching + daily rate-limit counters
- **Celery** — background tasks
- **JWT auth** (python-jose) + **bcrypt** (passlib)

**Frontend**
- **Vanilla JavaScript**, HTML, CSS, **Jinja2** templates
- **PWA** — service worker + web app manifest

**AI / External APIs**
- **Google Cloud Vision** (REST) — receipt OCR & ingredient image detection
- **TheMealDB** — recipe suggestions

**Data sources**
- **FoodSafety.gov** Cold Food Storage Chart — shelf-life estimates
- CO₂ emission factors (Poore & Nemecek, 2018) + typical Malaysian retail prices

**Infrastructure**
- **Docker** / docker-compose · deployed on **Render** (web + Postgres + Redis, auto HTTPS)

---

## Challenge & Approach

**The challenge:** Food waste is one of the largest, most overlooked contributors to household emissions. Existing pantry trackers fail because logging is manual, tedious, and offers no reason to come back.

**Our approach — remove friction, add motivation, prove impact:**

1. **Remove friction with AI.** Logging groceries is the #1 reason people quit. So we let users *scan a receipt or photo* — vision extracts the items, prices, and expiry dates automatically. Manual entry auto-fills shelf life from real food-safety data.
2. **Add motivation with a pet.** Behaviour change needs an emotional hook. A digital pet that **thrives when you rescue food and suffers when you waste it** turns an abstract goal into something you care about daily.
3. **Close the loop with recipes.** Knowing food is expiring isn't enough — we suggest recipes that *use those exact items first*, and update the pantry automatically when you cook.
4. **Prove the impact.** Every rescued item converts to real **CO₂ saved** (per-ingredient emission factors) and **money saved (RM)**, surfaced on a dashboard and a community leaderboard.

**Notable engineering challenges we solved**
- **Zero-cost AI path:** the receipt scanner prefers Google Vision but automatically falls back to the **free OCR.space API**, so the app fully works without any paid cloud billing.
- **Deploy without shell access:** database tables are **auto-created on startup**, so the app deploys cleanly on free hosting tiers with no migration step.
- **Honest failures:** scanners surface the real error and never silently inject fake data into your pantry.

---

## Usage

### Try it (deployed)
1. Open the live app and tap **Install** (or "Add to Home Screen") to get the PWA.
https://pantrypet.onrender.com
2. **Register** an account → your pet hatches.
3. **Add groceries**: scan a receipt, snap a photo, or add manually.
4. Check the **dashboard** for what's expiring, generate a **recipe**, and tap **Cooked** to clear used items.
5. Watch your **CO₂ / money saved** climb and your pet evolve. Compete on the **leaderboard**.



### Run locally
```bash
# 1. Clone
git clone <your-repo-url> && cd caffinated_coders

# 2. Start Postgres + Redis + the app
docker-compose up -d

# 3. (first run) create tables — or just let AUTO_INIT_DB do it on startup
docker-compose exec backend python init_db.py
docker-compose exec backend python seed.py   # optional demo data

# 4. Open the app
#    http://localhost:8000
```

Or without Docker (needs local Python 3.11, Postgres, Redis):
```bash
cd backend
python -m venv .venv && .venv/Scripts/activate   # (Windows)  |  source .venv/bin/activate (macOS/Linux)
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Environment variables
Create `backend/.env`:
```env
DATABASE_URL=postgresql+asyncpg://pantrypet:pantrypet123@localhost/pantrypet
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-me
# Optional — receipt OCR works for free without these:
OCR_SPACE_API_KEY=helloworld        # free; get your own at ocr.space/ocrapi // we used GoogleVision
GOOGLE_API_KEY=                      # only if you have Google Vision billing enabled
STRIPE_SECRET_KEY=                   # only for premium payments // only for future improvements / not implemented in this project
```

> The receipt scanner works out of the box using the free `helloworld` OCR.space key. Add a Google Vision key only if you have billing enabled.

---

# ai assistant usage
- "Code assistance provided by "Claude" for Project Structure and Deployment Assistance"
- "Code assistance provided by "Leonado.ai" for 2D sprite Design"