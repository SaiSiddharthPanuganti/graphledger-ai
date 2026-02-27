"""
Deliverable 4 — Audit Trail Generator
=======================================
Generates formal, explainable audit findings for GST reconciliation mismatches.

Each audit finding is:
  - Structured as a formal compliance document
  - Cites exact GST Act sections and CBIC circulars
  - Provides specific recommended actions
  - Formatted in plain text with ASCII box drawing

Output is suitable for:
  - Direct submission to GST authority
  - Internal compliance review
  - Generating ASMT-10 (Scrutiny notice response)
  - Evidence preservation in DGGI investigations
"""

from datetime import datetime
from typing import Optional
import re
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
try:
    from schema import MISMATCH_TAXONOMY
except ImportError:
    MISMATCH_TAXONOMY = {}


# ─── Indian Number Formatting ────────────────────────────────
def _inr(amount: float) -> str:
    """
    Format amount in Indian number system (lakhs/crores).
    INR 1,23,45,678 style formatting.
    """
    if amount >= 1_00_00_000:
        return f"INR {amount / 1_00_00_000:.2f} Crore"
    if amount >= 1_00_000:
        return f"INR {amount / 1_00_000:.2f} Lakh"
    # Indian comma formatting
    s = str(int(amount))
    if len(s) <= 3:
        return f"INR {s}"
    last3 = s[-3:]
    rest = s[:-3]
    parts = []
    while len(rest) > 2:
        parts.append(rest[-2:])
        rest = rest[:-2]
    if rest:
        parts.append(rest)
    formatted = ",".join(reversed(parts)) + "," + last3
    paise = f".{int((amount % 1) * 100):02d}"
    return f"INR {formatted}{paise}"


def _box(title: str, width: int = 72) -> str:
    """Draw ASCII box header."""
    inner = width - 2
    line  = "=" * inner
    pad   = max(0, (inner - len(title) - 2) // 2)
    return (
        f"+{line}+\n"
        f"| {' ' * pad}{title}{' ' * pad} {'|' if (inner - len(title) - 2) % 2 == 0 else ' |'}\n"
        f"+{line}+"
    )


def _section(title: str, width: int = 72) -> str:
    """Section divider."""
    dashes = "-" * (width - len(title) - 3)
    return f"+- {title} {dashes}"


GENERATION_TS = lambda: datetime.now().strftime("%d-%b-%Y %H:%M:%S IST")


# ─── Root Cause Library ──────────────────────────────────────
ROOT_CAUSES = {
    "AMOUNT_MISMATCH": (
        "Supplier filed an amendment return (GSTR-1A) correcting the invoice value "
        "without notifying the buyer. The amended value is reflected in GSTR-2B but "
        "the original value was recorded in the buyer's purchase register. Additionally, "
        "possible rounding errors in tax computation (CGST/SGST split) may contribute "
        "to minor discrepancies."
    ),
    "INVOICE_MISSING_2B": (
        "Supplier did not file GSTR-1 return for the relevant tax period, or filed "
        "the return after the GSTR-2B generation cut-off date (14th of the following month). "
        "Late-filed or amended GSTR-1 data is only reflected in the next available GSTR-2B. "
        "ITC eligibility under Section 16(2)(aa) is contingent on 2B reflection."
    ),
    "IRN_MISMATCH": (
        "Cryptographic validation of the Invoice Reference Number (IRN) has failed. "
        "Possible causes: (1) IRN was generated for a different invoice number/date, "
        "(2) IRN was cancelled on the IRP portal but the invoice continues to circulate, "
        "(3) IRN payload was tampered post-generation invalidating the SHA-256 hash, "
        "(4) Invoice is fabricated with a cloned/fake IRN. This is the highest-risk "
        "finding category and may indicate intent to commit ITC fraud under Section 132."
    ),
    "GSTIN_MISMATCH": (
        "The GSTIN of the buyer recorded on the physical invoice does not match the "
        "GSTIN under which ITC is being claimed. Common causes: incorrect GSTIN provided "
        "at the point of purchase, supplier used a branch GSTIN instead of the head office "
        "GSTIN, or the supplier's GSTIN was suspended/cancelled at the time of supply. "
        "ITC claimed under a different GSTIN is not admissible."
    ),
    "DATE_MISMATCH": (
        "Invoice date falls in Tax Period T but was reported by supplier in GSTR-1 for "
        "Period T+1 (or later). This causes a period mismatch — the invoice appears in "
        "GSTR-2B for a different month than the buyer's purchase register. Under "
        "Section 16(4), ITC must be claimed within the correct financial year."
    ),
    "EXTRA_IN_2B": (
        "Invoice appears in GSTR-2B (auto-populated from supplier's GSTR-1) but is "
        "absent from the buyer's purchase register. Possible causes: (1) Supplier "
        "uploaded a duplicate invoice, (2) Invoice was meant for a different GSTIN "
        "(similar name/address), (3) A cancelled invoice was not removed from GSTR-1, "
        "(4) Consignment was rejected/returned but return entry not processed."
    ),
    "EWAYBILL_MISSING": (
        "The consignment value exceeded the E-Way Bill threshold (INR 50,000 for "
        "interstate movement; state-specific thresholds for intrastate) but no valid "
        "E-Way Bill was generated before goods movement commenced. This may indicate "
        "that the underlying supply was not a physical transaction (possible paper "
        "transaction for ITC generation without actual goods movement)."
    ),
    "PAYMENT_OVERDUE_180_DAYS": (
        "The buyer has not paid the supplier the invoice value (including GST) within "
        "180 days of the invoice date. Under Section 16(2)(b) of the CGST Act 2017, "
        "this triggers a mandatory ITC reversal. The 180-day clock starts from the "
        "invoice date, not the date of delivery or receipt. "
        "This is one of the four mandatory eligibility conditions for ITC under Section 16(2). "
        "Common business reasons: extended credit terms (60-120 day credit periods), "
        "cash flow constraints, disputed invoices, or buyer insolvency. "
        "Regardless of the reason, GST law does not grant exceptions — ITC must be reversed "
        "in GSTR-3B Table 4(B)(2) of the period in which the 180th day falls."
    ),
}

# ─── Recommended Actions Library ─────────────────────────────
ACTIONS = {
    "AMOUNT_MISMATCH": [
        "Issue formal written notice to supplier within 7 working days requesting "
        "GSTR-1A amendment to correct invoice value.",
        "Provisionally reverse the excess ITC claimed in the next GSTR-3B filing "
        "(differential amount between GSTR-1 and GSTR-2B values).",
        "Do not reverse the GSTR-2B aligned portion — this remains eligible for ITC.",
        "Monitor GSTR-2B for the next period to confirm supplier has filed amendment.",
    ],
    "INVOICE_MISSING_2B": [
        "Immediately contact supplier's accounts/tax team to confirm GSTR-1 filing "
        "status for the relevant period on GST portal (services.gst.gov.in).",
        "Defer ITC claim for this invoice until it appears in GSTR-2B. Do NOT claim "
        "ITC in current GSTR-3B as it violates Section 16(2)(aa).",
        "If supplier files GSTR-1 within the current period, ITC may be claimed in "
        "the corresponding GSTR-3B after 2B is updated.",
        "If supplier persistently fails to file: consider adding GSTR-1 compliance "
        "clause to procurement contract with penalty provisions.",
    ],
    "IRN_MISMATCH": [
        "IMMEDIATE: Reverse all ITC claimed against this invoice in current GSTR-3B. "
        "Do not defer — invalid IRN = inadmissible ITC per Rule 48(4).",
        "Block payment to supplier pending IRN verification. Do not release funds "
        "until valid IRN is confirmed on IRP portal (einvoice1.gst.gov.in).",
        "Verify IRN authenticity directly on IRP portal using the invoice details. "
        "Screenshot and preserve verification result as evidence.",
        "If IRN is confirmed invalid/tampered: file complaint on GST portal "
        "(Section 154 application) and preserve all correspondence.",
        "Escalate to DGGI (Directorate General of GST Intelligence) if evidence "
        "of fabrication is found. Criminal prosecution possible under Section 132.",
    ],
    "GSTIN_MISMATCH": [
        "Verify actual GSTIN of supplier on GST portal GSTIN search tool. "
        "If suspended/cancelled: ITC is fully inadmissible.",
        "Request supplier to issue a fresh invoice with correct buyer GSTIN. "
        "Old invoice to be cancelled on IRP portal.",
        "Update procurement system with correct GSTIN to prevent recurrence.",
        "If correction not possible: reverse ITC; claim cannot be transferred "
        "between GSTINs even within the same legal entity.",
    ],
    "DATE_MISMATCH": [
        "Reconcile invoice date in purchase register against physical invoice copy.",
        "If invoice date is correct but period is wrong in supplier's GSTR-1: "
        "request GSTR-1A amendment from supplier.",
        "Defer ITC to the correct period as per Section 16(4) — claim within "
        "the same financial year as the invoice date.",
        "Update internal ERP to enforce period-lock at invoice booking stage.",
    ],
    "EXTRA_IN_2B": [
        "Cross-verify with supplier whether the extra 2B entry is a duplicate upload "
        "or a genuine supply not recorded by your team.",
        "If duplicate: supplier to cancel in GSTR-1A; 2B will be updated next cycle.",
        "If genuinely received: verify physical receipt and update purchase register.",
        "Do not claim ITC for this entry until purchase register is updated — "
        "ITC requires original invoice documentation per Rule 36(1).",
    ],
    "EWAYBILL_MISSING": [
        "Obtain E-Way Bill number from transporter/supplier and match with invoice.",
        "If no EWB was generated: document the reason (below threshold, exempt goods, "
        "own vehicle movement) and maintain records for potential audit queries.",
        "If goods were above threshold and EWB was missed: file self-disclosure with "
        "jurisdictional officer to avoid penalty under Rule 138F.",
        "ITC is not directly denied for missing EWB, but gaps in documentation "
        "increase scrutiny risk under Section 65/66 audit provisions.",
    ],
    "PAYMENT_OVERDUE_180_DAYS": [
        "IMMEDIATE: Reverse the full ITC amount in GSTR-3B Table 4(B)(2) of the "
        "current return period. Do not defer — every additional day accrues interest.",
        "Calculate interest at 18% p.a. from the date ITC was originally claimed "
        "to today (Section 50(3) CGST Act). Include this interest in GSTR-3B.",
        "Pay the supplier the full invoice amount (base value + GST) as soon as "
        "possible. Once paid, the ITC becomes re-claimable in that month's GSTR-3B.",
        "Document the payment (bank transfer / UTR number) as evidence for re-claim. "
        "The re-claim entry goes into GSTR-3B Table 4(A)(5) — ITC from previous periods.",
        "To prevent recurrence: implement a 150-day payment alert in your ERP system. "
        "Add GST compliance clause in vendor contracts requiring payment within 90 days.",
    ],
}

LEGAL_REFS = {
    "AMOUNT_MISMATCH":     ["Section 16(2)(c) CGST Act", "Rule 36(4) CGST Rules",
                            "CBIC Circular No. 183/15/2022"],
    "INVOICE_MISSING_2B":  ["Section 16(2)(aa) CGST Act (w.e.f. 01-Jan-2022)",
                            "Rule 36(4) CGST Rules", "CBIC Circular No. 170/02/2022"],
    "IRN_MISMATCH":        ["Rule 48(4) CGST Rules", "Section 122(1)(ii) CGST Act",
                            "Section 132 CGST Act — Criminal Prosecution",
                            "CBIC Notification No. 01/2020-CT"],
    "GSTIN_MISMATCH":      ["Section 16(1) CGST Act", "Section 25 CGST Act",
                            "Rule 46 CGST Rules — Tax Invoice requirements"],
    "DATE_MISMATCH":       ["Section 16(4) CGST Act — Time limit",
                            "Section 39(7) CGST Act", "Rule 59 CGST Rules"],
    "EXTRA_IN_2B":         ["Rule 36(1) CGST Rules", "Section 16(2) CGST Act",
                            "CBIC Circular No. 123/42/2019"],
    "EWAYBILL_MISSING":    ["Rule 138 CGST Rules", "Rule 138A CGST Rules",
                            "Section 129 CGST Act — Detention & Seizure",
                            "Rule 138F — E-Way Bill non-generation penalty"],
    "PAYMENT_OVERDUE_180_DAYS": [
                            "Section 16(2)(b) CGST Act 2017 — 180-day payment condition",
                            "Section 50(3) CGST Act — Interest on wrongly availed ITC",
                            "Rule 37 CGST Rules — Reversal of ITC on non-payment",
                            "GSTR-3B Table 4(B)(2) — ITC Reversal entry",
                            "CBIC Circular No. 170/02/2022 — ITC conditions clarification"],
}

ADMISSIBILITY = {
    "AMOUNT_MISMATCH":          "PARTIALLY AT RISK",
    "INVOICE_MISSING_2B":       "AT RISK — DEFER CLAIM",
    "IRN_MISMATCH":             "INADMISSIBLE — REVERSE IMMEDIATELY",
    "GSTIN_MISMATCH":           "INADMISSIBLE",
    "DATE_MISMATCH":            "AT RISK — PERIOD CORRECTION REQUIRED",
    "EXTRA_IN_2B":              "UNDER INVESTIGATION",
    "EWAYBILL_MISSING":         "ITC ELIGIBLE BUT AUDIT RISK",
    "PAYMENT_OVERDUE_180_DAYS": "INADMISSIBLE — REVERSE + PAY INTEREST (RE-CLAIMABLE ON PAYMENT)",
}


class AuditTrailGenerator:
    """Generates formal GST audit trail documents."""

    def generate_audit_trail(self, mismatch: dict) -> str:
        """
        Generate a formal audit finding document for a single mismatch.

        Args:
            mismatch: dict with keys:
                mismatch_id, mismatch_type, invoice_no, supplier_gstin,
                buyer_gstin, return_period, detected_date,
                gstr1_value (optional), gstr2b_value (optional),
                amount_at_risk, risk_level, resolution_status

        Returns:
            Formatted plain-text audit finding document
        """
        mtype   = mismatch.get("mismatch_type", "AMOUNT_MISMATCH")
        inv_no  = mismatch.get("invoice_no", "N/A")
        sup_gstin = mismatch.get("supplier_gstin", "N/A")
        buy_gstin = mismatch.get("buyer_gstin", "N/A")
        period  = mismatch.get("return_period", "N/A")
        det_date= mismatch.get("detected_date", datetime.now().strftime("%d-%b-%Y"))
        g1_val  = mismatch.get("gstr1_value", 0.0)
        g2b_val = mismatch.get("gstr2b_value", 0.0)
        at_risk = mismatch.get("amount_at_risk", 0.0)
        rlevel  = mismatch.get("risk_level", "HIGH")
        status  = mismatch.get("resolution_status", "PENDING")
        mid     = mismatch.get("mismatch_id", "MIS-001")

        variance     = abs(g1_val - g2b_val) if g1_val and g2b_val else at_risk
        variance_pct = (variance / g1_val * 100) if g1_val else 0.0
        prefix       = "[WARN]  CRITICAL FRAUD INDICATOR — " if mtype == "IRN_MISMATCH" else ""
        admissibility= ADMISSIBILITY.get(mtype, "AT RISK")

        lines = []

        # ── HEADER ──────────────────────────────────────────
        lines.append(_box(f"{prefix}AUDIT FINDING — {mtype.replace('_', ' ')}"))
        lines.append(f"  Reference No  : {mid}")
        lines.append(f"  Finding Type  : {mtype}")
        lines.append(f"  Invoice No    : {inv_no}")
        lines.append(f"  Supplier GSTIN: {sup_gstin}")
        lines.append(f"  Buyer GSTIN   : {buy_gstin}")
        lines.append(f"  Return Period : {period}")
        lines.append(f"  Detected Date : {det_date}")
        lines.append(f"  Risk Level    : {rlevel}")
        lines.append(f"  Status        : {status}")
        lines.append(f"  Generated     : {GENERATION_TS()}")
        lines.append("")

        # ── OBSERVATION ─────────────────────────────────────
        lines.append(_section("1. OBSERVATION"))
        if g1_val and g2b_val:
            lines.append(f"  GSTR-1 Value (as filed by supplier) : {_inr(g1_val)}")
            lines.append(f"  GSTR-2B Value (auto-populated)      : {_inr(g2b_val)}")
            lines.append(f"  Variance                            : {_inr(variance)} ({variance_pct:.1f}%)")
        else:
            lines.append(f"  ITC Amount at Risk                  : {_inr(at_risk)}")
        lines.append(f"  ITC Admissibility                   : {admissibility}")
        lines.append("")

        # ── ROOT CAUSE ──────────────────────────────────────
        lines.append(_section("2. ROOT CAUSE ANALYSIS"))
        root = ROOT_CAUSES.get(mtype, "Root cause under investigation.")
        for para in root.split(". "):
            if para.strip():
                # Word-wrap at 68 chars
                words = para.strip().split()
                line_buf, out = [], []
                for w in words:
                    if sum(len(x) + 1 for x in line_buf) + len(w) > 68:
                        out.append("  " + " ".join(line_buf))
                        line_buf = [w]
                    else:
                        line_buf.append(w)
                if line_buf:
                    out.append("  " + " ".join(line_buf))
                lines.extend(out)
        lines.append("")

        # ── ITC IMPACT ──────────────────────────────────────
        lines.append(_section("3. ITC IMPACT ASSESSMENT"))
        lines.append(f"  Total ITC at Risk    : {_inr(at_risk)}")
        lines.append(f"  ITC Admissibility    : {admissibility}")
        disallow_section = LEGAL_REFS.get(mtype, ["Section 16 CGST Act"])[0]
        lines.append(f"  Disallowance Basis   : {disallow_section}")
        if mtype == "IRN_MISMATCH":
            lines.append(f"  [WARN]  CRITICAL: Full ITC reversal required with 18% interest")
            lines.append(f"      per day from date of claim. Penalty may apply.")
        elif mtype == "INVOICE_MISSING_2B":
            lines.append(f"  NOTE: ITC may be claimed in future period once invoice")
            lines.append(f"        appears in GSTR-2B (Section 16(2)(aa) compliance).")
        elif mtype == "PAYMENT_OVERDUE_180_DAYS":
            days_overdue = mismatch.get("days_overdue", 0)
            interest     = mismatch.get("interest_liability", round(at_risk * 0.18 * (days_overdue / 365), 2))
            lines.append(f"  Days Since Invoice   : {days_overdue} days (threshold: 180 days)")
            lines.append(f"  Interest Liability   : {_inr(interest)} @ 18% p.a. (Section 50(3))")
            lines.append(f"  Total Liability      : {_inr(at_risk + interest)}")
            lines.append(f"  [WARN]  ITC is RE-CLAIMABLE once supplier payment is made.")
            lines.append(f"      Re-claim in GSTR-3B Table 4(A)(5) of payment month.")
        lines.append("")

        # ── RECOMMENDED ACTIONS ─────────────────────────────
        lines.append(_section("4. RECOMMENDED ACTIONS"))
        actions = ACTIONS.get(mtype, ["Investigate and resolve with supplier."])
        for i, action in enumerate(actions, 1):
            words = action.split()
            line_buf, out = [], []
            prefix_str = f"  {i}. "
            cont_prefix = "     "
            for w in words:
                if sum(len(x) + 1 for x in line_buf) + len(w) > 65:
                    pfx = prefix_str if not out else cont_prefix
                    out.append(pfx + " ".join(line_buf))
                    line_buf = [w]
                else:
                    line_buf.append(w)
            if line_buf:
                pfx = prefix_str if not out else cont_prefix
                out.append(pfx + " ".join(line_buf))
            lines.extend(out)
        lines.append("")

        # ── LEGAL REFERENCES ────────────────────────────────
        lines.append(_section("5. LEGAL REFERENCES"))
        for ref in LEGAL_REFS.get(mtype, ["Section 16 CGST Act 2017"]):
            lines.append(f"  • {ref}")
        lines.append(f"  • CGST Act 2017 — as amended up to Finance Act 2024")
        lines.append("")

        # ── RISK CLASSIFICATION ─────────────────────────────
        lines.append(_section("6. RISK CLASSIFICATION & ESCALATION"))
        escalation = {
            "CRITICAL": "ESCALATE IMMEDIATELY to CFO and Tax Compliance Head. "
                        "Initiate vendor audit under Section 65 CGST Act. "
                        "Preserve all invoice evidence for potential DGGI inquiry.",
            "HIGH":     "Escalate to Senior Tax Manager within 48 hours. "
                        "Initiate supplier communication and set 7-day resolution deadline.",
            "MEDIUM":   "Flag for next monthly compliance review. "
                        "Add to vendor watch list for enhanced monitoring.",
            "LOW":      "Record in compliance tracker. "
                        "Review at quarterly audit cycle.",
        }
        lines.append(f"  Risk Level  : {rlevel}")
        lines.append(f"  Escalation  : {escalation.get(rlevel, 'Review required.')}")
        lines.append("")
        lines.append("─" * 72)
        lines.append(f"  END OF AUDIT FINDING — {mid}")
        lines.append(f"  This document is auto-generated by GraphLedger AI v1.0")
        lines.append("─" * 72)

        return "\n".join(lines)

    def batch_audit_report(
        self,
        mismatches: list,
        company_name: str,
        report_period: str = "",
    ) -> str:
        """
        Generate a full audit report for multiple mismatches.
        Includes executive summary, individual findings, and action priority matrix.
        """
        ts          = GENERATION_TS()
        total       = len(mismatches)
        critical    = sum(1 for m in mismatches if m.get("risk_level") == "CRITICAL")
        high        = sum(1 for m in mismatches if m.get("risk_level") == "HIGH")
        total_risk  = sum(m.get("amount_at_risk", 0) for m in mismatches)
        irn_issues  = sum(1 for m in mismatches if m.get("mismatch_type") == "IRN_MISMATCH")

        lines = []
        lines.append(_box("GST ITC RECONCILIATION — AUDIT REPORT", width=76))
        lines.append(f"  Company         : {company_name}")
        lines.append(f"  Report Period   : {report_period or 'Multiple Periods'}")
        lines.append(f"  Generated On    : {ts}")
        lines.append(f"  Report Engine   : GraphLedger AI v1.0 — Knowledge Graph Analysis")
        lines.append("")
        lines.append("┌─ EXECUTIVE SUMMARY " + "─" * 52)
        lines.append(f"  Total Mismatches Found  : {total}")
        lines.append(f"  Critical Findings       : {critical}  [WARN]  IMMEDIATE ACTION REQUIRED")
        lines.append(f"  High Risk Findings      : {high}")
        lines.append(f"  Total ITC at Risk       : {_inr(total_risk)}")
        lines.append(f"  IRN Integrity Issues    : {irn_issues}  (potential fraud indicator)")
        lines.append("")

        # Mismatch type breakdown
        type_counts: dict = {}
        type_risk:   dict = {}
        for m in mismatches:
            t = m.get("mismatch_type", "UNKNOWN")
            type_counts[t] = type_counts.get(t, 0) + 1
            type_risk[t]   = type_risk.get(t, 0.0) + m.get("amount_at_risk", 0)

        lines.append("┌─ MISMATCH BREAKDOWN " + "─" * 51)
        lines.append(f"  {'Type':<25} {'Count':>6}  {'ITC at Risk':>18}  Risk")
        lines.append(f"  {'─'*24} {'─'*6}  {'─'*18}  {'─'*8}")
        for t in sorted(type_counts, key=lambda x: type_risk.get(x, 0), reverse=True):
            tax_info = MISMATCH_TAXONOMY.get(t, {})
            rlevel   = tax_info.get("risk_level", "MEDIUM")
            lines.append(f"  {t:<25} {type_counts[t]:>6}  {_inr(type_risk[t]):>18}  {rlevel}")
        lines.append("")

        # Individual findings
        lines.append("┌─ DETAILED FINDINGS " + "─" * 52)
        lines.append("")
        for idx, mismatch in enumerate(mismatches, 1):
            lines.append(f"FINDING {idx} OF {total}")
            lines.append(self.generate_audit_trail(mismatch))
            lines.append("")

        # Action priority matrix
        lines.append(_box("ACTION PRIORITY MATRIX", width=76))
        lines.append(f"  {'Priority':<12} {'Action':<45} {'Count':>5}")
        lines.append(f"  {'─'*11} {'─'*44} {'─'*5}")
        if critical > 0:
            lines.append(f"  {'P1-NOW':<12} Reverse ITC for CRITICAL findings immediately     {critical:>5}")
        if irn_issues > 0:
            lines.append(f"  {'P1-NOW':<12} Report IRN fraud to DGGI                         {irn_issues:>5}")
        if high > 0:
            lines.append(f"  {'P2-48HRS':<12} Vendor notice for HIGH risk mismatches            {high:>5}")
        medium = sum(1 for m in mismatches if m.get("risk_level") == "MEDIUM")
        if medium > 0:
            lines.append(f"  {'P3-7DAYS':<12} Monthly review for MEDIUM risk items              {medium:>5}")
        lines.append("")
        lines.append(f"  TOTAL ITC TO REVERSE IMMEDIATELY: {_inr(sum(m.get('amount_at_risk', 0) for m in mismatches if m.get('risk_level') == 'CRITICAL'))}")
        lines.append(f"  Total ITC at Risk (all findings) : {_inr(total_risk)}")
        lines.append("")
        lines.append("─" * 76)
        lines.append("  END OF BATCH AUDIT REPORT")
        lines.append(f"  Powered by GraphLedger AI — GST Knowledge Graph Intelligence Engine")
        lines.append("─" * 76)

        return "\n".join(lines)


# --- Demo / Test -----------------------------------------------------------
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    gen = AuditTrailGenerator()

    # Test data covering all 7 mismatch types
    test_mismatches = [
        {
            "mismatch_id": "MIS-001", "mismatch_type": "AMOUNT_MISMATCH",
            "invoice_no": "INV/2024/1042", "supplier_gstin": "27AABCT1332L1ZF",
            "buyer_gstin": "29AADCV5678B1ZP", "return_period": "102024",
            "detected_date": "14-Nov-2024", "gstr1_value": 850000.0,
            "gstr2b_value": 780000.0, "amount_at_risk": 70000.0,
            "risk_level": "HIGH", "resolution_status": "PENDING",
        },
        {
            "mismatch_id": "MIS-002", "mismatch_type": "INVOICE_MISSING_2B",
            "invoice_no": "TEC/2024/0387", "supplier_gstin": "33AAGCM2945B1ZR",
            "buyer_gstin": "27AABCM1234A1Z5", "return_period": "092024",
            "detected_date": "15-Oct-2024", "gstr1_value": 0, "gstr2b_value": 0,
            "amount_at_risk": 126000.0, "risk_level": "HIGH",
            "resolution_status": "IN_PROGRESS",
        },
        {
            "mismatch_id": "MIS-003", "mismatch_type": "IRN_MISMATCH",
            "invoice_no": "SHL/2024/0019", "supplier_gstin": "07AABCS9876D1ZK",
            "buyer_gstin": "27AABCM1234A1Z5", "return_period": "112024",
            "detected_date": "16-Dec-2024", "gstr1_value": 2400000.0,
            "gstr2b_value": 2400000.0, "amount_at_risk": 432000.0,
            "risk_level": "CRITICAL", "resolution_status": "PENDING",
        },
        {
            "mismatch_id": "MIS-004", "mismatch_type": "GSTIN_MISMATCH",
            "invoice_no": "MFG/2024/2211", "supplier_gstin": "24AAACR5055K1ZF",
            "buyer_gstin": "27AABCM1234A1Z5", "return_period": "082024",
            "detected_date": "14-Sep-2024", "amount_at_risk": 95000.0,
            "risk_level": "HIGH", "resolution_status": "PENDING",
        },
        {
            "mismatch_id": "MIS-005", "mismatch_type": "DATE_MISMATCH",
            "invoice_no": "SVC/2024/0891", "supplier_gstin": "29AAGFK1234N1ZQ",
            "buyer_gstin": "27AABCM1234A1Z5", "return_period": "072024",
            "detected_date": "15-Aug-2024", "amount_at_risk": 34200.0,
            "risk_level": "MEDIUM", "resolution_status": "RESOLVED",
        },
        {
            "mismatch_id": "MIS-006", "mismatch_type": "EXTRA_IN_2B",
            "invoice_no": "LOG/2024/0456", "supplier_gstin": "06AAACL7891B1ZM",
            "buyer_gstin": "27AABCM1234A1Z5", "return_period": "102024",
            "detected_date": "14-Nov-2024", "amount_at_risk": 18000.0,
            "risk_level": "MEDIUM", "resolution_status": "IN_PROGRESS",
        },
        {
            "mismatch_id": "MIS-007", "mismatch_type": "EWAYBILL_MISSING",
            "invoice_no": "TRD/2024/1105", "supplier_gstin": "09AABFT4561C1ZN",
            "buyer_gstin": "27AABCM1234A1Z5", "return_period": "112024",
            "detected_date": "16-Dec-2024", "amount_at_risk": 22500.0,
            "risk_level": "MEDIUM", "resolution_status": "PENDING",
        },
    ]

    print("=" * 72)
    print("  AUDIT TRAIL GENERATOR — ALL 7 MISMATCH TYPE DEMONSTRATIONS")
    print("=" * 72)

    for m in test_mismatches:
        print(f"\n\n{'-'*72}")
        print(f"  GENERATING: {m['mismatch_type']}")
        print(f"{'-'*72}")
        print(gen.generate_audit_trail(m))

    print("\n\n" + "=" * 72)
    print("  BATCH AUDIT REPORT DEMONSTRATION")
    print("=" * 72)
    batch = gen.batch_audit_report(
        test_mismatches[:3],
        company_name="Mahindra Auto Parts Manufacturing Ltd",
        report_period="Q3 FY 2024-25 (Oct–Dec 2024)",
    )
    print(batch)
