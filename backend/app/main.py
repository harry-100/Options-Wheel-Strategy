from fastapi import FastAPI
from app.api import strategies
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Wheel Strategy AI Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:5173"] for stricter security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register endpoints
app.include_router(strategies.router, prefix="/api/strategy")
