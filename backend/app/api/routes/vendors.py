"""Vendor intelligence endpoints."""
from fastapi import APIRouter
from app.services.risk_engine import get_all_vendor_risk_profiles, compute_vendor_risk_profile
from app.services.mock_data import store

router = APIRouter()


@router.get("")
def list_vendors():
    """List all vendors with compliance scores and risk profiles."""
    return get_all_vendor_risk_profiles()


@router.get("/{vendor_id}")
def get_vendor(vendor_id: str):
    """
    Full vendor risk profile: compliance score, filing behavior,
    invoice statistics, risk flags, and at-risk ITC exposure.
    """
    store.initialize()
    profile  = compute_vendor_risk_profile(vendor_id)
    invoices = store.get_invoices_for_vendor(vendor_id)

    # Attach invoice summary
    profile["invoices"] = [
        {
            "invoice_id":    i["invoice_id"],
            "invoice_date":  i["invoice_date"],
            "period":        i["period"],
            "total_gst":     i["total_gst"],
            "status":        i["status"],
            "risk_category": i["risk_category"],
            "risk_score":    i["risk_score"],
        }
        for i in sorted(invoices, key=lambda x: x["risk_score"], reverse=True)
    ]
    return profile
