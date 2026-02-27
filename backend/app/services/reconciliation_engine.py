"""
GraphLedger AI — Multi-Hop Reconciliation Engine
==================================================
Simulates the Cypher graph traversal:

  MATCH (t:Taxpayer)-[:PURCHASED]->(inv:Invoice)
        -[:ISSUED_BY]->(v:Vendor)
  OPTIONAL MATCH (inv)-[:HAS_IRN]->(irn:IRN)
  OPTIONAL MATCH (inv)-[:REFLECTED_IN]->(g2b:GSTR2B)
  OPTIONAL MATCH (v)-[:FILED]->(g1:GSTR1 {period: inv.period})
  RETURN inv, v, irn, g2b, g1

Each hop validates one layer of the ITC reconciliation chain:
  Hop 1: Taxpayer → Invoice       (is this our purchase?)
  Hop 2: Invoice → Vendor         (who is the seller?)
  Hop 3: Invoice → IRN            (is e-invoice valid?)
  Hop 4: Invoice → GSTR-2B        (is it auto-populated in our purchase register?)
  Hop 5: Vendor → GSTR-1          (has vendor filed sales return?)
  Hop 6: GSTR-3B → Payment        (has tax been deposited?)

Why graph traversal is superior to SQL JOINs:
  - SQL JOIN complexity grows as O(n²) per hop
  - Graph traversal is O(k) where k = number of connections
  - SQL cannot naturally detect cycles (circular trading)
  - Graph algorithms (PageRank, Louvain) are native to Neo4j
  - Pattern matching in Cypher is declarative and readable
"""

from app.services.mock_data import store
from app.services.audit_engine import generate_audit_report


def reconcile_invoice(invoice_id: str) -> dict:
    """
    Run full multi-hop reconciliation for a single invoice.
    Returns validation result with hop-by-hop breakdown.
    """
    store.initialize()
    invoice = store.get_invoice_by_id(invoice_id)
    if not invoice:
        return {"error": f"Invoice {invoice_id} not found"}

    vendor = store.get_vendor_by_id(invoice["vendor_id"])

    # Simulate each traversal hop
    hops = [
        {
            "hop":         1,
            "traversal":   "Taxpayer → Invoice",
            "cypher":      f"MATCH (t:Taxpayer {{gstin: '{store.taxpayer['gstin']}'}})-[:PURCHASED]->(inv:Invoice {{invoice_id: '{invoice_id}'}})",
            "status":      "PASS",
            "detail":      f"Invoice {invoice_id} is a valid purchase record for {store.taxpayer['name']}",
        },
        {
            "hop":         2,
            "traversal":   "Invoice → Vendor",
            "cypher":      "MATCH (inv)-[:ISSUED_BY]->(v:Vendor)",
            "status":      "PASS",
            "detail":      f"Vendor: {invoice['vendor_name']} | GSTIN: {invoice['vendor_gstin']} | Score: {invoice['vendor_score']}",
        },
        {
            "hop":         3,
            "traversal":   "Invoice → IRN (E-Invoice Validation)",
            "cypher":      "OPTIONAL MATCH (inv)-[:HAS_IRN]->(irn:IRN)",
            "status":      "PASS" if invoice["irn_valid"] else "FAIL",
            "detail":      (
                f"IRN: {invoice['irn_number'][:16]}... (valid)"
                if invoice["irn_valid"]
                else "IRN not found or invalid — e-invoice mandate violated"
            ),
        },
        {
            "hop":         4,
            "traversal":   "Invoice → GSTR-2B (Purchase Register)",
            "cypher":      "OPTIONAL MATCH (inv)-[:REFLECTED_IN]->(g2b:GSTR2B)",
            "status":      "PASS" if invoice["in_gstr2b"] else "FAIL",
            "detail":      (
                f"Invoice reflected in GSTR-2B for period {invoice['period']}"
                if invoice["in_gstr2b"]
                else f"Invoice NOT in GSTR-2B for period {invoice['period']} — ITC at risk"
            ),
        },
        {
            "hop":         5,
            "traversal":   "Vendor → GSTR-1 (Sales Return Filing)",
            "cypher":      f"OPTIONAL MATCH (v)-[:FILED]->(g1:GSTR1 {{period: '{invoice['period']}'}})",
            "status":      "PASS" if invoice["vendor_filed"] else "FAIL",
            "detail":      (
                f"Vendor filed GSTR-1 for period {invoice['period']}"
                if invoice["vendor_filed"]
                else f"Vendor did NOT file GSTR-1 for period {invoice['period']} — NON-FILER"
            ),
        },
        {
            "hop":         6,
            "traversal":   "GSTR-3B → Payment (Tax Deposit)",
            "cypher":      "OPTIONAL MATCH (g3b:GSTR3B)-[:SETTLED_BY]->(pmt:Payment)",
            "status":      "PASS" if invoice["tax_paid"] else "FAIL",
            "detail":      (
                "Tax payment confirmed in challan register"
                if invoice["tax_paid"]
                else "Tax payment NOT confirmed — ITC chain broken at payment"
            ),
        },
    ]

    passed = sum(1 for h in hops if h["status"] == "PASS")
    failed = sum(1 for h in hops if h["status"] == "FAIL")

    audit = generate_audit_report(invoice)

    return {
        "invoice_id":     invoice_id,
        "reconciliation_status": invoice["status"],
        "risk_category":  invoice["risk_category"],
        "risk_score":     invoice["risk_score"],
        "hops_passed":    passed,
        "hops_failed":    failed,
        "traversal_hops": hops,
        "audit_report":   audit,
        "gst_amount":     invoice["total_gst"],
        "itc_safe":       invoice["risk_category"] == "LOW",
    }


def reconcile_all_invoices(
    limit: int = 100,
    risk_filter: str | None = None,
    vendor_filter: str | None = None,
) -> dict:
    """
    Run reconciliation across all invoices with optional filtering.
    Returns paginated results with summary statistics.
    """
    store.initialize()

    invoices = store.invoices
    if risk_filter:
        invoices = [i for i in invoices if i["risk_category"] == risk_filter.upper()]
    if vendor_filter:
        invoices = [i for i in invoices if i["vendor_id"] == vendor_filter]

    # Sort by risk score descending (most at-risk first)
    invoices = sorted(invoices, key=lambda x: x["risk_score"], reverse=True)[:limit]

    results = []
    for inv in invoices:
        audit = generate_audit_report(inv)
        results.append({
            "invoice_id":       inv["invoice_id"],
            "invoice_number":   inv["invoice_number"],
            "invoice_date":     inv["invoice_date"],
            "period":           inv["period"],
            "vendor_id":        inv["vendor_id"],
            "vendor_name":      inv["vendor_name"],
            "vendor_score":     inv["vendor_score"],
            "gst_rate":         inv["gst_rate"],
            "total_gst":        inv["total_gst"],
            "total_amount":     inv["total_amount"],
            "irn_valid":        inv["irn_valid"],
            "in_gstr2b":        inv["in_gstr2b"],
            "vendor_filed":     inv["vendor_filed"],
            "tax_paid":         inv["tax_paid"],
            "status":           inv["status"],
            "risk_score":       inv["risk_score"],
            "risk_category":    inv["risk_category"],
            "risk_reasons":     inv["risk_reasons"],
            "finding_count":    audit["finding_count"],
            "recommended_action": audit["recommended_action"],
            "is_circular_trade": inv.get("is_circular_trade", False),
        })

    return {
        "total":   len(store.invoices),
        "filtered":len(results),
        "invoices":results,
    }
