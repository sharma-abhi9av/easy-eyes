import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import engine, Base, SessionLocal
import app.models
from app.seed import seed_database
from app.routers import auth, products, cart, orders, admin, reviews


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Easy Eyes — Luxury Eyewear API",
    description="REST API for Easy Eyes E-Commerce (GDG Hackathon)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(GZipMiddleware, minimum_size=500)


@app.middleware("http")
async def security_and_cache_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    path = request.url.path
    if path.startswith("/static/images/") or path.startswith("/static/fonts/"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    elif path.startswith("/static/css/") or path.startswith("/static/js/"):
        response.headers["Cache-Control"] = "public, max-age=86400"
    return response


app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(admin.router)
app.include_router(reviews.router)


@app.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "ok", "brand": "Easy Eyes"}


STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
@app.get("/index.html", include_in_schema=False)
def serve_home():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/product.html", include_in_schema=False)
def serve_product():
    return FileResponse(os.path.join(STATIC_DIR, "product.html"))


@app.get("/cart.html", include_in_schema=False)
def serve_cart():
    return FileResponse(os.path.join(STATIC_DIR, "cart.html"))


@app.get("/login.html", include_in_schema=False)
def serve_login():
    return FileResponse(os.path.join(STATIC_DIR, "login.html"))


@app.get("/admin.html", include_in_schema=False)
def serve_admin():
    return FileResponse(os.path.join(STATIC_DIR, "admin.html"))
