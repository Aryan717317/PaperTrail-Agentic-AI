"""
app/main.py

FastAPI entrypoint for PaperTrail. Mounts modular API routers.
"""

import logging
from fastapi import FastAPI

from app.api import documents, health, research

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("papertrail")

app = FastAPI(
    title="PaperTrail",
    description="Evidence-grounded research paper intelligence & verification platform",
    version="0.2.0",
)

app.include_router(health.router)
app.include_router(documents.router)
app.include_router(research.router)
