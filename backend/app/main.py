"""
FastAPI Main Application for GPA Calculator AI Agent.
Serves both the REST API and the frontend HTML/CSS/JS from the same server.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv

load_dotenv()

from .database import init_db
from .routes.calculator_routes import router as calc_router
from .routes.history_routes import router as hist_router
from .routes.chat_routes import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="GPA Calculator AI Agent API",
    description="Deterministic GPA engine + AI academic advisor for SPPU CBCS engineering students.",
    version="1.0.0",
    lifespan=lifespan
)

# Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(calc_router)
app.include_router(hist_router)
app.include_router(chat_router)


@app.get("/api/health", status_code=status.HTTP_200_OK, tags=["System"])
def health_check():
    api_key = os.getenv("OPENAI_API_KEY", "")
    ai_configured = bool(
        api_key
        and api_key != "your_openai_api_key_here"
        and not api_key.startswith("sk-placeholder")
    )
    return {
        "status": "healthy",
        "service": "GPA Calculator AI Agent",
        "ai_configured": ai_configured,
        "calculation_engine": "deterministic_python_v1",
        "database": "sqlite_ready"
    }


# ── Static file serving ──────────────────────────────────────────────────────
# Compute absolute path to the frontend directory (sibling of backend/)
_backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # backend/
_project_root = os.path.dirname(_backend_root)                                  # gpa-calculator-ai/
FRONTEND_DIR = os.path.join(_project_root, "frontend")

if os.path.isdir(FRONTEND_DIR):
    # Mount CSS and JS sub-directories so relative URLs work correctly
    app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
    app.mount("/js",  StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")),  name="js")

    @app.get("/", include_in_schema=False)
    @app.get("/index.html", include_in_schema=False)
    def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    @app.get("/landing", include_in_schema=False)
    @app.get("/landing.html", include_in_schema=False)
    def serve_landing():
        return FileResponse(os.path.join(FRONTEND_DIR, "landing.html"))

    @app.get("/landing.css", include_in_schema=False)
    def serve_landing_css():
        return FileResponse(os.path.join(FRONTEND_DIR, "landing.css"), media_type="text/css")

    @app.get("/landing.js", include_in_schema=False)
    def serve_landing_js():
        return FileResponse(os.path.join(FRONTEND_DIR, "landing.js"), media_type="application/javascript")

    @app.get("/favicon.ico", include_in_schema=False)
    def favicon():
        return JSONResponse({}, status_code=204)
else:
    @app.get("/", include_in_schema=False)
    def root():
        return {"message": "GPA Calculator AI Agent API running. Visit /docs for Swagger UI."}
