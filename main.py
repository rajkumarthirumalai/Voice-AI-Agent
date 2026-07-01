import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import HTMLResponse, RedirectResponse

from app.config import settings
from app.api.routes import router as api_router
from app.api.websockets import router as ws_router
from app.database.connection import db_manager
from app.core.session import session_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("voice_agent")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB connection pool and Redis connection
    logger.info("Initializing database connection pool...")
    await db_manager.initialize()
    
    logger.info("Initializing session storage connection...")
    await session_manager.initialize()
    
    yield
    
    # Shutdown: Clean up connections
    logger.info("Closing database connection pool...")
    await db_manager.close()
    
    logger.info("Closing session storage connection...")
    await session_manager.close()

app = FastAPI(
    title="Bilingual Voice AI Agent (Hall Booking)",
    description="Real-time voice assistant handling Tamil and English streams for booking halls.",
    version="1.0.0",
    lifespan=lifespan,
)

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root_app():
    """
    Serves the main Voice AI Agent console dashboard application.
    """
    with open("app/templates/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

# Enable CORS for frontend and testing tools
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust as needed in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(ws_router, tags=["WebSockets"])
app.include_router(api_router, prefix="/api/v1", tags=["REST API"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
