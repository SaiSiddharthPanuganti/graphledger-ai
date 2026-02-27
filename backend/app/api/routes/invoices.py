"""Invoice reconciliation endpoints."""
from fastapi import APIRouter, Query
from typing import Optional
from app.services.reconciliation_engine import reconcile_all_invoices, reconcile_invoice

router = APIRouter()


@router.get("")
def list_invoices(
    risk: Optional[str] = Query(None, description="Filter by risk category: LOW|MEDIUM|HIGH|CRITICAL"),
    vendor: Optional[str] = Query(None, description="Filter by vendor ID e.g. V001"),
    limit: int = Query(100, le=100),
):
    """
    List all invoices with reconciliation status and risk scores.
    Supports filtering by risk category and vendor.
    """
    return reconcile_all_invoices(limit=limit, risk_filter=risk, vendor_filter=vendor)


@router.get("/{invoice_id}")
def get_invoice(invoice_id: str):
    """
    Full multi-hop reconciliation report for a single invoice.
    Returns hop-by-hop traversal result + explainable audit report.
    """
    return reconcile_invoice(invoice_id)
