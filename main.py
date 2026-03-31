import os
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv

from orchestrator import orchestrator
from agents.tracker_agent import mark_resolved
from agents.database_agent import get_all_complaints, get_product_stats
from agents.manufacturer_agent import get_pending_contacts
from agents.learning_agent import improve

load_dotenv()

# Setup logging for Cloud Run
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ResolveX API",
    description="Autonomous multi-agent customer care system",
    version="1.0.0"
)

# Allow all origins for hackathon demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Startup Event ─────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """Verify critical environment variables on startup."""
    required = ["GOOGLE_CLOUD_PROJECT"]
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        logger.error(f"[main] Missing required env vars: {missing}")
    else:
        logger.info("[main] ResolveX API started successfully")
        logger.info(f"[main] Project: {os.getenv('GOOGLE_CLOUD_PROJECT')}")


# ── Request Models ────────────────────────────────────────────

class ComplaintRequest(BaseModel):
    complaint: str

    @field_validator("complaint")
    @classmethod
    def validate_complaint(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError("Complaint must be at least 10 characters")
        if len(v) > 5000:
            raise ValueError("Complaint must be under 5000 characters")
        return v.strip()


class ProductRequest(BaseModel):
    product_name: str

    @field_validator("product_name")
    @classmethod
    def validate_product_name(cls, v):
        if not v or len(v.strip()) < 1:
            raise ValueError("Product name cannot be empty")
        if len(v) > 200:
            raise ValueError("Product name must be under 200 characters")
        return v.strip()


# ── Routes ────────────────────────────────────────────────────

@app.get("/")
def root():
    """API root — lists all available endpoints."""
    return {
        "name": "ResolveX",
        "status": "running",
        "description": "Autonomous multi-agent customer care system",
        "version": "1.0.0",
        "endpoints": {
            "POST /complaint": "Submit a customer complaint",
            "GET  /dashboard": "Get full dashboard data",
            "GET  /complaints": "Get all complaints",
            "GET  /products": "Get product return statistics",
            "POST /tracker/run": "Trigger tracker for a product",
            "POST /manufacturer/resolve": "Mark manufacturer issue as resolved",
            "GET  /manufacturer/pending": "Get all unresolved manufacturer contacts",
            "POST /learning/run": "Manually trigger learning agent",
            "GET  /health": "Health check"
        }
    }


@app.get("/health")
def health():
    """Health check for Cloud Run."""
    return {
        "status": "healthy",
        "project": os.getenv("GOOGLE_CLOUD_PROJECT", "not set")
    }


@app.post("/complaint")
def submit_complaint(request: ComplaintRequest):
    """
    Main endpoint. Submit a customer complaint and
    receive a full autonomous resolution.
    """
    logger.info(f"[main] New complaint received: {request.complaint[:50]}...")

    try:
        result = orchestrator.handle_complaint(request.complaint)
        logger.info(f"[main] Complaint resolved: {result.get('complaint_id')}")
        return {
            "success": True,
            "complaint_id": result.get("complaint_id"),
            "customer_response": result.get("customer_response"),
            "steps_completed": list(result.get("steps", {}).keys())
        }
    except Exception as e:
        logger.error(f"[main] Complaint handling failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboard")
def get_dashboard():
    """Returns all data needed for the live dashboard."""
    logger.info("[main] Dashboard data requested")
    try:
        data = orchestrator.get_dashboard_data()
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"[main] Dashboard fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/complaints")
def list_complaints():
    """Returns all complaints ordered by most recent."""
    logger.info("[main] Complaints list requested")
    try:
        complaints = get_all_complaints()
        return {
            "success": True,
            "complaints": complaints,
            "total": len(complaints)
        }
    except Exception as e:
        logger.error(f"[main] Complaints fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/products")
def list_product_stats():
    """Returns product return statistics ordered by most complaints."""
    logger.info("[main] Product stats requested")
    try:
        stats = get_product_stats()
        return {
            "success": True,
            "products": stats,
            "total": len(stats)
        }
    except Exception as e:
        logger.error(f"[main] Product stats fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tracker/run")
def run_tracker(request: ProductRequest):
    """Manually trigger the tracker agent for a specific product."""
    logger.info(f"[main] Tracker triggered for: {request.product_name}")
    try:
        result = orchestrator.run_tracker(request.product_name)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"[main] Tracker failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/manufacturer/resolve")
def resolve_manufacturer_issue(request: ProductRequest):
    """
    Mark a manufacturer issue as resolved.
    Automatically notifies all affected customers.
    """
    logger.info(f"[main] Marking resolved: {request.product_name}")
    try:
        result = mark_resolved(request.product_name)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"[main] Mark resolved failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/manufacturer/pending")
def get_pending_manufacturer_contacts():
    """Returns all manufacturer contacts awaiting resolution."""
    logger.info("[main] Pending manufacturer contacts requested")
    try:
        pending = get_pending_contacts()
        return {
            "success": True,
            "pending": pending,
            "total": len(pending)
        }
    except Exception as e:
        logger.error(f"[main] Pending contacts fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/learning/run")
def run_learning():
    """Manually trigger the learning agent to analyze patterns."""
    logger.info("[main] Learning agent manually triggered")
    try:
        result = improve()
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"[main] Learning agent failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    try:
        port = int(os.getenv("PORT", "8080"))
    except ValueError:
        port = 8080
        logger.warning("[main] PORT env var invalid — defaulting to 8080")

    logger.info(f"[main] Starting server on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)