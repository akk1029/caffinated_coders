import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from app.core.config import settings
from app.routers import auth, inventory, recipes, payments, pet
from app.routers import receipts, dashboard, leaderboard, uploads

_HERE = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered pantry management with a digital pet companion",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=os.path.join(_HERE, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(_HERE, "templates"))

# ─── API routes ───────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api")
app.include_router(inventory.router, prefix="/api")
app.include_router(recipes.router, prefix="/api")
app.include_router(payments.router, prefix="/api")
app.include_router(pet.router, prefix="/api")
app.include_router(receipts.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(leaderboard.router, prefix="/api")
app.include_router(uploads.router, prefix="/api")

# ─── Page routes (serve HTML) ─────────────────────────────────────────────────
@app.get("/", response_class=RedirectResponse)
async def root():
    return RedirectResponse(url="/dashboard")

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse(request, "dashboard.html")

@app.get("/inventory", response_class=HTMLResponse)
async def inventory_page(request: Request):
    return templates.TemplateResponse(request, "inventory.html")

@app.get("/recipes", response_class=HTMLResponse)
async def recipes_page(request: Request):
    return templates.TemplateResponse(request, "recipes.html")

@app.get("/pet", response_class=HTMLResponse)
async def pet_page(request: Request):
    return templates.TemplateResponse(request, "pet.html")

@app.get("/premium", response_class=HTMLResponse)
async def premium_page(request: Request):
    return templates.TemplateResponse(request, "premium.html")

@app.get("/leaderboard", response_class=HTMLResponse)
async def leaderboard_page(request: Request):
    return templates.TemplateResponse(request, "leaderboard.html")

@app.get("/hatch", response_class=HTMLResponse)
async def hatch_page(request: Request):
    return templates.TemplateResponse(request, "hatch.html")

@app.get("/sw.js")
async def get_sw():
    return FileResponse(os.path.join(_HERE, "static", "sw.js"), media_type="application/javascript")
