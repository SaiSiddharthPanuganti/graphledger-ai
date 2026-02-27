"""
Bonus — FastAPI REST API connecting all 5 Deliverables
=======================================================
Exposes all engine functionality as HTTP endpoints.

Architecture:
  Startup: load GSTKnowledgeGraph → initialize AuditTrailGenerator
           + VendorRiskPredictor (singleton pattern)

  All endpoints return consistent JSON with:
    { "status": "ok", "data": {...} }
  or on error:
    { "status": "error", "detail": "..." }
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from typing import Optional

from schema import NODE_TYPES, EDGE_SCHEMA, MISMATCH_TAXONOMY
from data_generator import generate_all, DATA_DIR
from reconciliation_engine import GSTKnowledgeGraph
from audit_trail import AuditTrailGenerator
from risk_predictor import VendorRiskPredictor

# ─── App Initialization ───────────────────────────────────────
app = FastAPI(
    title="GraphLedger AI — GST Knowledge Graph API",
    description=(
        "REST API for India's GST ITC Reconciliation Engine. "
        "Powered by NetworkX Knowledge Graph + Rule-Based Risk Intelligence."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Singletons ───────────────────────────────────────────────
kg        = GSTKnowledgeGraph()
audit_gen = AuditTrailGenerator()
predictor: Optional[VendorRiskPredictor] = None


@app.on_event("startup")
async def startup():
    global predictor
    # Generate data if not present
    if not (DATA_DIR / "invoices.json").exists():
        print("Generating mock data...")
        generate_all()
    kg.load_data()
    predictor = VendorRiskPredictor(kg)
    print(f"✅ API ready. Graph: {kg.G.number_of_nodes()} nodes, "
          f"{kg.G.number_of_edges()} edges")


def _ok(data) -> dict:
    return {"status": "ok", "data": data}


def _check_gstin(gstin: str):
    if not kg.G.has_node(f"gstin_{gstin}"):
        raise HTTPException(status_code=404, detail=f"GSTIN {gstin} not found in graph")


# ═══════════════════════════════════════════════════════════════
# HEALTH
# ═══════════════════════════════════════════════════════════════

@app.get("/api/health")
def health():
    return _ok({
        "graph_loaded": kg.G.number_of_nodes() > 0,
        "nodes":        kg.G.number_of_nodes(),
        "edges":        kg.G.number_of_edges(),
        "vendors":      len(kg.vendors),
        "invoices":     len(kg.invoices),
        "mismatches":   len(kg.mismatches),
    })


# ═══════════════════════════════════════════════════════════════
# DELIVERABLE 1 — Schema
# ═══════════════════════════════════════════════════════════════

@app.get("/api/schema")
def get_schema():
    """Returns full node/edge schema and mismatch taxonomy."""
    return _ok({
        "node_types": {
            name: list(cls.__annotations__.keys())
            for name, cls in NODE_TYPES.items()
        },
        "edge_types": {
            name: {
                "source":     meta["source"],
                "target":     meta["target"],
                "properties": meta["properties"],
                "description":meta["description"],
            }
            for name, meta in EDGE_SCHEMA.items()
        },
        "mismatch_taxonomy": {
            mtype: {
                "risk_level":        info["risk_level"],
                "itc_impact":        info["itc_impact"],
                "itc_risk_multiplier":info["itc_risk_multiplier"],
                "legal_reference":   info["legal_reference"],
                "description":       info["description"],
            }
            for mtype, info in MISMATCH_TAXONOMY.items()
        },
    })


# ═══════════════════════════════════════════════════════════════
# DELIVERABLE 2 — Reconciliation Engine
# ═══════════════════════════════════════════════════════════════

@app.get("/api/reconcile/{gstin}")
def reconcile(
    gstin: str,
    period: str = Query("102024", description="Return period MMYYYY"),
    risk_filter: Optional[str] = Query(None, description="Filter by risk level: CRITICAL/HIGH/MEDIUM/LOW"),
):
    """
    Runs reconciliation for a GSTIN and period.
    Returns match_rate, total_itc_at_risk, classified mismatches.
    """
    _check_gstin(gstin)
    result = kg.reconcile_period(gstin, period)
    if risk_filter:
        result["classified_mismatches"] = [
            m for m in result["classified_mismatches"]
            if m["risk_level"] == risk_filter.upper()
        ]
    return _ok(result)


@app.get("/api/mismatches")
def get_mismatches(
    risk: Optional[str]  = Query(None, description="Risk level filter"),
    type: Optional[str]  = Query(None, alias="type", description="Mismatch type filter"),
    limit: int           = Query(50, le=200),
):
    """Returns filtered mismatch list with total ITC at risk."""
    results = kg.mismatches
    if risk:
        results = [m for m in results if m["risk_level"] == risk.upper()]
    if type:
        results = [m for m in results if m["mismatch_type"] == type.upper()]
    results = sorted(results, key=lambda x: x["amount_at_risk"], reverse=True)[:limit]
    total_at_risk = sum(m["amount_at_risk"] for m in results)
    return _ok({
        "total":          len(results),
        "total_itc_at_risk": total_at_risk,
        "mismatches":     results,
    })


@app.get("/api/itc/chain/{gstin}")
def itc_chain(
    gstin: str,
    max_hops: int = Query(4, ge=1, le=6, description="Maximum traversal hops"),
):
    """Returns full ITC chain traversal result with hop-by-hop detail."""
    _check_gstin(gstin)
    return _ok(kg.validate_itc_chain(gstin, max_hops=max_hops))


@app.get("/api/graph/stats")
def graph_stats():
    """Returns node count, edge count, node type breakdown."""
    return _ok(kg.get_graph_stats())


@app.get("/api/graph/clusters")
def graph_clusters():
    """Returns top 10 risk clusters with member GSTINs."""
    return _ok({"clusters": kg.find_risk_clusters()})


# ═══════════════════════════════════════════════════════════════
# DELIVERABLE 3 — Dashboard
# ═══════════════════════════════════════════════════════════════

@app.get("/api/dashboard/summary")
def dashboard_summary():
    """Returns all KPIs: match rate, ITC at risk, critical count, mismatch breakdown."""
    mis = kg.mismatches
    total_risk     = sum(m["amount_at_risk"] for m in mis)
    critical_count = sum(1 for m in mis if m["risk_level"] == "CRITICAL")

    type_breakdown = {}
    for m in mis:
        t = m["mismatch_type"]
        if t not in type_breakdown:
            type_breakdown[t] = {"count": 0, "total_itc_at_risk": 0.0}
        type_breakdown[t]["count"]           += 1
        type_breakdown[t]["total_itc_at_risk"] += m["amount_at_risk"]

    resolved = sum(1 for m in mis if m["resolution_status"] == "RESOLVED")

    return _ok({
        "kpis": {
            "total_invoices":       len(kg.invoices),
            "total_mismatches":     len(mis),
            "critical_findings":    critical_count,
            "total_itc_at_risk":    round(total_risk, 2),
            "match_rate":           round((1 - len(mis) / max(1, len(kg.invoices))) * 100, 1),
            "resolution_rate":      round(resolved / max(1, len(mis)) * 100, 1),
        },
        "mismatch_by_type": type_breakdown,
        "graph_stats": kg.get_graph_stats(),
    })


@app.get("/api/vendors/risk")
def vendors_risk(
    category: Optional[str] = Query(None, description="Risk category filter"),
    sector:   Optional[str] = Query(None, description="Sector filter"),
):
    """Returns vendor risk profiles with optional filtering."""
    results = kg.vendors
    if category:
        results = [v for v in results if v["risk_category"] == category.upper()]
    if sector:
        results = [v for v in results if v.get("sector", "").lower() == sector.lower()]
    return _ok({"total": len(results), "vendors": results})


# ═══════════════════════════════════════════════════════════════
# DELIVERABLE 4 — Audit Trail
# ═══════════════════════════════════════════════════════════════

@app.get("/api/audit/{mismatch_id}", response_class=PlainTextResponse)
def audit_single(mismatch_id: str):
    """Generates and returns natural language audit trail for one mismatch."""
    m = kg._mis_index.get(mismatch_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Mismatch {mismatch_id} not found")
    return audit_gen.generate_audit_trail(m)


@app.post("/api/audit/batch")
def audit_batch(gstin: str = Query(..., description="GSTIN to generate batch audit for")):
    """Generates full audit report for all mismatches of a GSTIN."""
    _check_gstin(gstin)
    tp_data = kg._gstin_to_tp.get(gstin, {})
    company = tp_data.get("name", gstin)
    gstin_mis = [m for m in kg.mismatches if m["supplier_gstin"] == gstin or
                 m.get("buyer_gstin") == gstin]
    if not gstin_mis:
        raise HTTPException(status_code=404, detail=f"No mismatches found for {gstin}")
    report = audit_gen.batch_audit_report(gstin_mis, company_name=company)
    return {"status": "ok", "data": {"report": report, "finding_count": len(gstin_mis)}}


# ═══════════════════════════════════════════════════════════════
# DELIVERABLE 5 — Predictions
# ═══════════════════════════════════════════════════════════════

@app.get("/api/predict/{gstin}")
def predict_vendor(gstin: str):
    """Returns next-period risk prediction with graph features and key factors."""
    _check_gstin(gstin)
    result = predictor.predict_next_period_risk(gstin)
    result["explanation"] = predictor.explain_prediction(gstin)
    return _ok(result)


@app.get("/api/predict/all")
def predict_all(top_n: int = Query(10, ge=1, le=50)):
    """Returns predictions for all vendors, top N by predicted risk score."""
    result = predictor.predict_all_vendors()
    result["predictions"] = result["predictions"][:top_n]
    return _ok(result)


# ── OCR Upload Router ─────────────────────────────────────────────
from fastapi import UploadFile, File
from ocr_engine import InvoiceOCREngine

ocr_engine_instance = InvoiceOCREngine()

@app.post("/api/ocr/upload")
async def ocr_upload(file: UploadFile = File(...)):
    """Upload a PDF or image invoice for OCR extraction and GSTR-2B validation."""
    content = await file.read()
    filename = file.filename or "upload"
    ext = filename.lower().rsplit(".", 1)[-1]

    if ext == "pdf":
        result = ocr_engine_instance.extract_from_pdf(content, filename)
    elif ext in ("png", "jpg", "jpeg", "tiff", "bmp"):
        result = ocr_engine_instance.extract_from_image(content, filename)
    else:
        raise HTTPException(status_code=422, detail=f"Unsupported file type: .{ext}. Use PDF or image.")

    return result

@app.get("/api/ocr/history")
def ocr_history():
    """Return all previously uploaded invoice OCR results."""
    return {"uploads": ocr_engine_instance.get_history(), "stats": ocr_engine_instance.get_summary_stats()}

@app.get("/api/ocr/stats")
def ocr_stats():
    return ocr_engine_instance.get_summary_stats()

@app.post("/api/ocr/text")
async def ocr_from_text(payload: dict):
    """Accept raw invoice text for field extraction (useful for testing)."""
    text = payload.get("text", "")
    filename = payload.get("filename", "pasted_text")
    if not text:
        raise HTTPException(status_code=422, detail="text field required")
    return ocr_engine_instance.extract_from_text(text, filename)

@app.get("/api/ocr/sample-invoices")
def list_sample_invoices():
    """List all generated sample invoices available for download/testing."""
    from pathlib import Path
    sample_dir = Path("sample_invoices")
    if not sample_dir.exists():
        return {"invoices": [], "message": "Run invoice_generator.py to create samples"}
    files = [{"name": f.name, "size_kb": round(f.stat().st_size/1024, 1)} for f in sample_dir.glob("*.pdf")]
    return {"invoices": files}


# ═══════════════════════════════════════════════════════════════
# CHATBOT — Groq AI Assistant
# ═══════════════════════════════════════════════════════════════
from pydantic import BaseModel
from chat_engine import chat as groq_chat

# In-memory session store: session_id → history list
_chat_sessions: dict = {}

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """
    AI chatbot powered by Groq (llama-3.3-70b-versatile).
    Supports multi-turn conversation and live GST data tool calls.

    Request:  { "message": "...", "session_id": "user123" }
    Response: { "reply": "...", "session_id": "...", "turn": N }
    """
    history = _chat_sessions.get(req.session_id, [])

    try:
        reply, new_history = groq_chat(
            user_message=req.message,
            history=history,
            kg=kg,
            predictor=predictor,
        )
        _chat_sessions[req.session_id] = new_history[-20:]  # Keep last 20 turns
        return {
            "status": "ok",
            "reply": reply,
            "session_id": req.session_id,
            "turn": len([m for m in new_history if m.get("role") == "assistant"]),
        }
    except Exception as e:
        # Auto-clear corrupted session so the next message starts fresh
        _chat_sessions.pop(req.session_id, None)
        return {"status": "error", "reply": f"⚠️ AI service error: {str(e)}", "session_id": req.session_id}


@app.delete("/api/chat/{session_id}")
def clear_chat_session(session_id: str):
    """Clear conversation history for a session."""
    _chat_sessions.pop(session_id, None)
    return {"status": "ok", "message": f"Session '{session_id}' cleared"}


# ─── Main ─────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8001))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=False)
