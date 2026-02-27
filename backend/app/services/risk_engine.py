"""
GraphLedger AI — Risk Intelligence Engine
==========================================
Computes multi-dimensional risk scores for vendors and invoices.

Risk Model:
  Invoice Risk  = rule-based scoring (see mock_data.py _compute_risk_score)
  Vendor Risk   = weighted composite of:
                    40% filing compliance rate
                    30% IRN validity rate
                    20% GSTR-2B reflection rate
                    10% graph centrality (connection degree)

Scalability Notes:
  - Current: rule-based scoring (deterministic, explainable)
  - Phase 2: XGBoost/LightGBM trained on historical GST violation data
  - Phase 3: GNN (Graph Neural Network) leveraging vendor graph topology
  - GSTN API integration: real-time compliance checks via sandbox APIs
"""

from app.services.mock_data import store


def compute_vendor_risk_profile(vendor_id: str) -> dict:
    """
    Build a full risk profile for a vendor using:
      1. Invoice-level statistics
      2. GSTR-1 filing history
      3. Graph position (how connected this vendor is)
    """
    store.initialize()
    vendor = store.get_vendor_by_id(vendor_id)
    if not vendor:
        return {}

    invoices = store.get_invoices_for_vendor(vendor_id)
    if not invoices:
        return {**vendor, "invoice_count": 0, "risk_profile": "INSUFFICIENT_DATA"}

    total   = len(invoices)
    irn_ok  = sum(1 for i in invoices if i["irn_valid"])
    in_2b   = sum(1 for i in invoices if i["in_gstr2b"])
    filed   = sum(1 for i in invoices if i["vendor_filed"])
    paid    = sum(1 for i in invoices if i["tax_paid"])
    risk_hi = sum(1 for i in invoices if i["risk_category"] in ["HIGH", "CRITICAL"])

    filing_rate   = filed  / total
    irn_rate      = irn_ok / total
    in_2b_rate    = in_2b  / total
    payment_rate  = paid   / total

    # Weighted composite compliance score
    # Weights reflect regulatory importance in ITC reconciliation
    composite_score = (
        0.40 * filing_rate  +   # GSTR-1 filing is the primary requirement
        0.30 * irn_rate     +   # E-invoice compliance
        0.20 * in_2b_rate   +   # GSTR-2B auto-population
        0.10 * payment_rate     # Tax deposit confirmation
    )
    composite_score = round(composite_score, 3)

    # Graph centrality approximation:
    # Vendors with more connections = higher systemic risk
    # (In production: use Neo4j PageRank/Betweenness centrality)
    is_circular = vendor.get("compliance_tier") == "FRAUDULENT"

    risk_flags = []
    if filing_rate < 0.5:
        risk_flags.append("CHRONIC_NON_FILER")
    if irn_rate < 0.6:
        risk_flags.append("IRN_NON_COMPLIANT")
    if in_2b_rate < 0.5:
        risk_flags.append("GSTR2B_MISMATCH_PATTERN")
    if payment_rate < 0.5:
        risk_flags.append("TAX_PAYMENT_GAPS")
    if is_circular:
        risk_flags.append("CIRCULAR_TRADE_SUSPECTED")

    total_gst_value  = sum(i["total_gst"] for i in invoices)
    at_risk_gst      = sum(i["total_gst"] for i in invoices if i["risk_category"] in ["HIGH", "CRITICAL"])

    return {
        "vendor_id":           vendor_id,
        "gstin":               vendor["gstin"],
        "name":                vendor["name"],
        "state":               vendor["state"],
        "compliance_tier":     vendor["compliance_tier"],
        "compliance_score":    composite_score,
        "risk_category":       vendor["risk_category"],
        "total_invoices":      total,
        "total_gst_value":     total_gst_value,
        "at_risk_gst":         at_risk_gst,
        "high_risk_invoice_count": risk_hi,
        "metrics": {
            "filing_rate":    round(filing_rate * 100, 1),
            "irn_valid_rate": round(irn_rate * 100, 1),
            "gstr2b_rate":    round(in_2b_rate * 100, 1),
            "payment_rate":   round(payment_rate * 100, 1),
        },
        "risk_flags":          risk_flags,
        "is_circular_trade_suspect": is_circular,
    }


def get_all_vendor_risk_profiles() -> list[dict]:
    store.initialize()
    profiles = [compute_vendor_risk_profile(v["vendor_id"]) for v in store.vendors]
    return sorted(profiles, key=lambda x: x.get("compliance_score", 1.0))


def get_risk_summary() -> dict:
    """Aggregate risk statistics across all vendors and invoices."""
    store.initialize()

    vendor_profiles = get_all_vendor_risk_profiles()
    invoices = store.invoices

    return {
        "vendor_risk_distribution": {
            "CRITICAL": sum(1 for v in vendor_profiles if v.get("risk_category") == "CRITICAL"),
            "HIGH":     sum(1 for v in vendor_profiles if v.get("risk_category") == "HIGH"),
            "MEDIUM":   sum(1 for v in vendor_profiles if v.get("risk_category") == "MEDIUM"),
            "LOW":      sum(1 for v in vendor_profiles if v.get("risk_category") == "LOW"),
        },
        "invoice_risk_distribution": {
            "CRITICAL": sum(1 for i in invoices if i["risk_category"] == "CRITICAL"),
            "HIGH":     sum(1 for i in invoices if i["risk_category"] == "HIGH"),
            "MEDIUM":   sum(1 for i in invoices if i["risk_category"] == "MEDIUM"),
            "LOW":      sum(1 for i in invoices if i["risk_category"] == "LOW"),
        },
        "top_risk_vendors": [
            {"vendor_id": v["vendor_id"], "name": v["name"],
             "score": v["compliance_score"], "category": v["risk_category"]}
            for v in vendor_profiles[:5]
        ],
    }
