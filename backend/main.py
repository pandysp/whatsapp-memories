from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import messages
import logging
import os

# Configure basic logging
# logging.basicConfig(level=logging.INFO) # Removed this line
logger = logging.getLogger(__name__)

app = FastAPI(
    title="WhatsApp Memories API",
    description="API for accessing processed WhatsApp chat data.",
    version="0.1.0",
)

# CORS configuration for cross-origin requests from frontend
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000"  # Default for local development
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
# app.include_router(messages.router, prefix="/api") # Old way
app.include_router(messages.exchanges_router, prefix="/api")
app.include_router(messages.messages_router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    # You can add any async startup tasks here, e.g., initializing DB connection pools if needed
    # For now, cache_utils handles its own DB init on first use.
    pass


@app.on_event("shutdown")
async def shutdown_event():
    pass


@app.get("/health", tags=["General"])
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy"}


# If you intend to run this directly using `python backend/main.py` for dev,
# you might add:
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
