import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from orchestrator import orchestrator
from agents.tracker_agent import mark_resolved

load_dotenv()

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


# ── Request Models ─────────────────────────────────────────────

class ComplaintRequest(BaseModel):
    complaint: str


class ResolveRequest(BaseModel):
    product_name: str


class TrackerRequest(BaseModel):
    product_name: str


# ── Routes ────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "name": "ResolveX",
        "status": "running",
        "description": "Autonomous multi-agent customer care system",
        "version": "1.0.0"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/complaint")
def submit_complaint(request: ComplaintRequest):
    """
    Main endpoint. Submit a customer complaint and get
    a full resolution back.
    """
    if not request.complaint or len(request.complaint.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="Complaint must be at least 10 characters"
        )

    try:
        result = orchestrator.handle_complaint(request.complaint)
        return {
            "success": True,
            "complaint_id": result.get("complaint_id"),
            "customer_response": result.get("customer_response"),
            "steps_completed": list(result.get("steps", {}).keys())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboard")
def get_dashboard():
    """Returns all dashboard data."""
    try:
        data = orchestrator.get_dashboard_data()
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tracker/run")
def run_tracker(request: TrackerRequest):
    """Manually trigger tracker for a product."""
    try:
        result = orchestrator.run_tracker(request.product_name)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/manufacturer/resolve")
def resolve_manufacturer_issue(request: ResolveRequest):
    """
    Mark a manufacturer issue as resolved.
    Triggers customer notifications automatically.
    """
    try:
        result = mark_resolved(request.product_name)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/complaints")
def get_complaints():
    """Returns all complaints."""
    try:
        from agents.database_agent import get_all_complaints
        complaints = get_all_complaints()
        return {"success": True, "complaints": complaints, "total": len(complaints)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/products")
def get_product_stats():
    """Returns product return statistics."""
    try:
        from agents.database_agent import get_product_stats
        stats = get_product_stats()
        return {"success": True, "products": stats, "total": len(stats)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)