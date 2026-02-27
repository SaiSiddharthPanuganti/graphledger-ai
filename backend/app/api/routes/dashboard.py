"""Dashboard summary endpoints."""
from fastapi import APIRouter
from app.services.mock_data import store
from app.services.risk_engine import get_risk_summary

router = APIRouter()


@router.get("/summary")
def get_summary():
    """
    Executive summary KPIs for the main dashboard.
    Returns: total ITC, risk breakdown, vendor stats, mismatch %.
    """
    store.initialize()
    summary = store.get_dashboard_summary()
    risk    = get_risk_summary()
    trend   = store.get_period_trend()
    dist    = store.get_risk_distribution()

    return {
        "kpis":    summary,
        "risk_distribution":   dist,
        "vendor_risk":         risk["vendor_risk_distribution"],
        "period_trend":        trend,
        "top_risk_vendors":    risk["top_risk_vendors"],
    }


@router.get("/taxpayer")
def get_taxpayer():
    store.initialize()
    return store.taxpayer
