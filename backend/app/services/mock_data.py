"""
GraphLedger AI — Mock Data Generator
=====================================
Generates a realistic GST ecosystem simulation:
  • 1  Taxpayer  (the company claiming ITC)
  • 20 Vendors   (sellers supplying goods/services)
  • 100 Invoices (30% with mismatch/risk scenarios)
  • GSTR-1, GSTR-2B, GSTR-3B for each period
  • IRNs (e-invoice reference numbers)
  • 1 circular trading ring (3 suspicious vendors)
  • Financial risk scores for every entity

This module is the single source of truth for all mock data.
Both the FastAPI routes and any future Neo4j seeding use this.

GST BACKGROUND (for newcomers):
  A buyer can claim Input Tax Credit (ITC) only if:
    1. The vendor has uploaded the invoice in GSTR-1
    2. The invoice appears in buyer's GSTR-2B (auto-populated)
    3. The invoice has a valid IRN (e-invoice reference)
    4. The vendor has actually paid the GST collected
  Any break in this chain = ITC disallowance + penalty risk
"""

import random
import hashlib
from datetime import datetime, timedelta
from typing import Any

random.seed(42)  # Reproducible data for demos


# ─── GST Constants ───────────────────────────────────────────
STATES = {
    "27": "Maharashtra", "29": "Karnataka", "07": "Delhi",
    "33": "Tamil Nadu",  "24": "Gujarat",   "06": "Haryana",
    "09": "Uttar Pradesh", "19": "West Bengal", "36": "Telangana",
    "32": "Kerala",
}
PERIODS = ["2024-07", "2024-08", "2024-09", "2024-10", "2024-11", "2024-12"]
BUYER_GSTIN = "27AABCM1234A1Z5"  # Taxpayer's GSTIN


def _make_gstin(state_code: str, pan_suffix: str) -> str:
    """Generate a realistic-looking GSTIN. Format: SS + 10-char-PAN + 1 + Z + C"""
    pan = f"AAB{pan_suffix}A"
    return f"{state_code}{pan}1Z{random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')}"


def _make_irn(invoice_id: str, vendor_gstin: str, date: str) -> str:
    """IRN is a 64-char SHA-256 hash of: seller_gstin + doc_type + doc_number + doc_date"""
    raw = f"{vendor_gstin}INV{invoice_id}{date}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _random_date(period: str) -> str:
    """Random date within a given YYYY-MM period."""
    year, month = map(int, period.split("-"))
    days_in_month = 28 if month == 2 else 30 if month in [4, 6, 9, 11] else 31
    day = random.randint(1, days_in_month)
    return f"{year}-{month:02d}-{day:02d}"


# ─── Vendor Profiles ─────────────────────────────────────────
VENDOR_PROFILES = [
    # (id, name, state, compliance_tier, filing_behavior)
    # compliance_tier: "EXCELLENT" | "GOOD" | "AVERAGE" | "POOR" | "FRAUDULENT"
    ("V001", "Tata Components Ltd",       "27", "EXCELLENT", "always"),
    ("V002", "Infosys BPO Services",      "29", "EXCELLENT", "always"),
    ("V003", "Reliance Industries Sup.",  "24", "EXCELLENT", "always"),
    ("V004", "HDFC Logistics Pvt Ltd",    "07", "EXCELLENT", "always"),
    ("V005", "Mahindra Logistics Ltd",    "27", "GOOD",      "always"),
    ("V006", "Wipro Tech Supplies",       "29", "GOOD",      "always"),
    ("V007", "Bajaj Auto Components",     "27", "GOOD",      "always"),
    ("V008", "Larsen & Toubro Parts",     "33", "GOOD",      "always"),
    ("V009", "Asian Paints Materials",    "27", "AVERAGE",   "mostly"),
    ("V010", "Havells Electrical",        "06", "AVERAGE",   "mostly"),
    ("V011", "Dixon Tech Components",     "09", "AVERAGE",   "mostly"),
    ("V012", "Sundaram Fasteners",        "33", "AVERAGE",   "mostly"),
    ("V013", "VIP Industries Supplies",   "19", "AVERAGE",   "mostly"),
    ("V014", "Minda Industries Ltd",      "06", "POOR",      "sometimes"),
    ("V015", "Amara Raja Components",     "36", "POOR",      "sometimes"),
    ("V016", "Exide Industries Sup.",     "19", "POOR",      "rarely"),
    ("V017", "Subros Cooling Systems",    "09", "POOR",      "rarely"),
    # Circular trading ring — V018, V019, V020
    ("V018", "ShellCo Trading Hub",       "07", "FRAUDULENT","never"),
    ("V019", "Phantom Supplies Pvt",      "07", "FRAUDULENT","never"),
    ("V020", "Mirage Enterprises",        "07", "FRAUDULENT","never"),
]

COMPLIANCE_CONFIG = {
    "EXCELLENT":  {"score_range": (0.88, 0.98), "irn_valid_pct": 0.99, "in_2b_pct": 0.99, "filing_pct": 1.00, "paid_pct": 1.00},
    "GOOD":       {"score_range": (0.70, 0.87), "irn_valid_pct": 0.95, "in_2b_pct": 0.93, "filing_pct": 0.96, "paid_pct": 0.95},
    "AVERAGE":    {"score_range": (0.45, 0.69), "irn_valid_pct": 0.80, "in_2b_pct": 0.75, "filing_pct": 0.80, "paid_pct": 0.82},
    "POOR":       {"score_range": (0.20, 0.44), "irn_valid_pct": 0.55, "in_2b_pct": 0.50, "filing_pct": 0.45, "paid_pct": 0.50},
    "FRAUDULENT": {"score_range": (0.05, 0.18), "irn_valid_pct": 0.20, "in_2b_pct": 0.15, "filing_pct": 0.00, "paid_pct": 0.10},
}


def _vendor_risk_category(score: float) -> str:
    if score >= 0.75: return "LOW"
    if score >= 0.50: return "MEDIUM"
    if score >= 0.25: return "HIGH"
    return "CRITICAL"


def generate_vendors() -> list[dict]:
    vendors = []
    for vid, name, state_code, tier, _ in VENDOR_PROFILES:
        cfg = COMPLIANCE_CONFIG[tier]
        pan_suffix = f"DC{vid[1:]}00"[:7]  # deterministic PAN fragment
        gstin = _make_gstin(state_code, pan_suffix)
        score = round(random.uniform(*cfg["score_range"]), 3)
        vendors.append({
            "vendor_id":          vid,
            "gstin":              gstin,
            "name":               name,
            "state_code":         state_code,
            "state":              STATES.get(state_code, "Unknown"),
            "compliance_tier":    tier,
            "compliance_score":   score,
            "risk_category":      _vendor_risk_category(score),
            "filing_frequency":   "Monthly",
            "irn_valid_pct":      cfg["irn_valid_pct"],
            "in_2b_pct":          cfg["in_2b_pct"],
            "filing_pct":         cfg["filing_pct"],
            "paid_pct":           cfg["paid_pct"],
            "historical_mismatch_rate": round(1 - cfg["in_2b_pct"], 2),
        })
    return vendors


def generate_taxpayer() -> dict:
    return {
        "gstin":           BUYER_GSTIN,
        "name":            "Mahindra Auto Parts Manufacturing Ltd",
        "state_code":      "27",
        "state":           "Maharashtra",
        "pan":             "AABCM1234A",
        "annual_turnover": 150_000_000,
        "taxpayer_type":   "Regular",
        "registration_date": "2017-07-01",
    }


def _compute_risk_score(
    irn_valid: bool, in_2b: bool, vendor_filed: bool,
    tax_paid: bool, amount_mismatch: bool, vendor_score: float
) -> tuple[int, str, list[str]]:
    """
    Rule-based risk scoring engine.
    Returns (score: 0-100, category: str, reasons: list[str])

    Scoring weights (designed to reflect real GST audit risk):
      IRN invalid       → +40  (e-invoice mandate violation)
      Not in GSTR-2B   → +30  (ITC disallowance likely)
      Vendor non-filer  → +35  (CRITICAL — vendor hasn't paid GST)
      Tax unpaid        → +35  (direct liability on buyer)
      Amount mismatch   → +20  (reconciliation gap)
      Vendor score adj. → up to +10 (penalty for chronic offenders)
    """
    score = 0
    reasons = []

    if not irn_valid:
        score += 40
        reasons.append("IRN validation failed — e-invoice mandate violation")
    if not in_2b:
        score += 30
        reasons.append("Invoice not reflected in GSTR-2B — ITC disallowance risk")
    if not vendor_filed:
        score += 35
        reasons.append("Vendor has not filed GSTR-1 — GST not deposited upstream")
    if not tax_paid:
        score += 35
        reasons.append("Tax payment not confirmed — circular ITC chain broken")
    if amount_mismatch:
        score += 20
        reasons.append("Invoice amount mismatch between GSTR-1 and GSTR-2B")

    # Chronic bad vendor penalty
    if vendor_score < 0.30:
        score += 10
        reasons.append(f"Vendor compliance score critically low ({vendor_score:.2f})")

    score = min(score, 100)

    if score >= 70:
        category = "CRITICAL"
    elif score >= 45:
        category = "HIGH"
    elif score >= 20:
        category = "MEDIUM"
    else:
        category = "LOW"

    return score, category, reasons


def generate_invoices(vendors: list[dict]) -> list[dict]:
    """
    Generate 100 invoices with realistic mismatch distribution:
      ~70% CLEAN invoices
      ~10% missing IRN
      ~8%  not in GSTR-2B
      ~7%  vendor non-filer
      ~5%  amount mismatch
    Circular trading invoices: 5 invoices among V018/V019/V020
    """
    invoices = []
    vendor_map = {v["vendor_id"]: v for v in vendors}

    # Assign invoice counts per vendor (total = 100)
    invoice_assignments = []
    # Circular trading vendors get 5 invoices total
    circular_vendors = ["V018", "V019", "V020"]
    for vid in circular_vendors:
        count = random.randint(1, 2)
        invoice_assignments.extend([vid] * count)

    # Remaining 95 across other vendors
    other_vendors = [v["vendor_id"] for v in vendors if v["vendor_id"] not in circular_vendors]
    while len(invoice_assignments) < 100:
        invoice_assignments.append(random.choice(other_vendors))
    random.shuffle(invoice_assignments)
    invoice_assignments = invoice_assignments[:100]

    for idx, vendor_id in enumerate(invoice_assignments, 1):
        vendor = vendor_map[vendor_id]
        period = random.choice(PERIODS)
        inv_date = _random_date(period)
        base_amount = random.choice([
            random.randint(10_000, 50_000),
            random.randint(50_000, 2_00_000),
            random.randint(2_00_000, 10_00_000),
        ])
        gst_rate = random.choice([0.05, 0.12, 0.18, 0.28])
        gst_amount = round(base_amount * gst_rate)
        is_interstate = vendor["state_code"] != "27"  # buyer is Maharashtra (27)

        # Probabilistic compliance flags based on vendor tier
        irn_valid    = random.random() < vendor["irn_valid_pct"]
        in_2b        = irn_valid and (random.random() < vendor["in_2b_pct"])
        vendor_filed = random.random() < vendor["filing_pct"]
        tax_paid     = vendor_filed and (random.random() < vendor["paid_pct"])
        amount_mismatch = (not in_2b) and (random.random() < 0.3)

        # Circular trading vendors: override flags to be mostly invalid
        if vendor_id in circular_vendors:
            irn_valid       = random.random() < 0.20
            in_2b           = False
            vendor_filed    = False
            tax_paid        = False
            amount_mismatch = True

        risk_score, risk_category, risk_reasons = _compute_risk_score(
            irn_valid, in_2b, vendor_filed, tax_paid,
            amount_mismatch, vendor["compliance_score"]
        )

        # Determine reconciliation status
        if risk_category == "LOW":
            status = "MATCHED"
        elif risk_category == "MEDIUM":
            status = "PARTIAL_MATCH"
        else:
            status = "MISMATCHED"

        invoice_id  = f"INV-{idx:03d}"
        inv_number  = f"{vendor_id}/2024/{idx:04d}"
        irn_number  = _make_irn(invoice_id, vendor["gstin"], inv_date) if irn_valid else None

        invoices.append({
            "invoice_id":       invoice_id,
            "invoice_number":   inv_number,
            "invoice_date":     inv_date,
            "period":           period,
            "vendor_id":        vendor_id,
            "vendor_gstin":     vendor["gstin"],
            "vendor_name":      vendor["name"],
            "vendor_score":     vendor["compliance_score"],
            "vendor_tier":      vendor["compliance_tier"],
            "taxable_amount":   base_amount,
            "gst_rate":         int(gst_rate * 100),
            "cgst":             0 if is_interstate else gst_amount // 2,
            "sgst":             0 if is_interstate else gst_amount // 2,
            "igst":             gst_amount if is_interstate else 0,
            "total_gst":        gst_amount,
            "total_amount":     base_amount + gst_amount,
            "is_interstate":    is_interstate,
            "irn_number":       irn_number,
            "irn_valid":        irn_valid,
            "in_gstr2b":        in_2b,
            "vendor_filed":     vendor_filed,
            "tax_paid":         tax_paid,
            "amount_mismatch":  amount_mismatch,
            "status":           status,
            "risk_score":       risk_score,
            "risk_category":    risk_category,
            "risk_reasons":     risk_reasons,
            "is_circular_trade": vendor_id in circular_vendors,
        })

    return invoices


def generate_gstr_returns(vendors: list[dict], invoices: list[dict]) -> dict:
    """Generate GSTR-1 (vendor), GSTR-2B (buyer auto), GSTR-3B (buyer filed)"""
    vendor_map = {v["vendor_id"]: v for v in vendors}

    gstr1_records = []
    for period in PERIODS:
        for vendor in vendors:
            period_invoices = [i for i in invoices
                               if i["vendor_id"] == vendor["vendor_id"] and i["period"] == period]
            if not period_invoices:
                continue
            filed = vendor["filing_pct"] > 0.5 and random.random() < vendor["filing_pct"]
            # Filing date = 11th of next month (due date for GSTR-1)
            year, month = map(int, period.split("-"))
            next_month = month + 1 if month < 12 else 1
            next_year  = year if month < 12 else year + 1
            due_date   = f"{next_year}-{next_month:02d}-11"
            late_days  = random.randint(0, 15) if not filed else 0
            filing_date = None
            if filed:
                base = datetime.strptime(due_date, "%Y-%m-%d")
                filing_date = (base + timedelta(days=late_days)).strftime("%Y-%m-%d")

            gstr1_records.append({
                "gstr1_id":     f"GSTR1-{vendor['vendor_id']}-{period}",
                "vendor_id":    vendor["vendor_id"],
                "vendor_gstin": vendor["gstin"],
                "period":       period,
                "filing_date":  filing_date,
                "filed":        filed,
                "invoice_count":len(period_invoices),
                "total_tax_value": sum(i["total_gst"] for i in period_invoices),
            })

    # GSTR-2B: auto-populated for buyer (only invoices in 2B)
    gstr2b_records = []
    for period in PERIODS:
        in_2b_invoices = [i for i in invoices
                          if i["period"] == period and i["in_gstr2b"]]
        gstr2b_records.append({
            "gstr2b_id":       f"GSTR2B-BUYER-{period}",
            "period":          period,
            "generated_date":  f"{period[:4]}-{int(period[5:]):02d}-14",  # 14th of next month
            "invoice_count":   len(in_2b_invoices),
            "total_itc_available": sum(i["total_gst"] for i in in_2b_invoices),
        })

    # GSTR-3B: filed by buyer
    gstr3b_records = []
    for period in PERIODS:
        period_invoices = [i for i in invoices if i["period"] == period]
        itc_claimed = sum(i["total_gst"] for i in period_invoices if i["in_gstr2b"])
        year, month = map(int, period.split("-"))
        next_month = month + 1 if month < 12 else 1
        next_year  = year if month < 12 else year + 1
        gstr3b_records.append({
            "gstr3b_id":   f"GSTR3B-BUYER-{period}",
            "period":      period,
            "filing_date": f"{next_year}-{next_month:02d}-20",
            "filed":       True,
            "itc_claimed": itc_claimed,
            "tax_paid":    max(0, itc_claimed - random.randint(100_000, 500_000)),
        })

    return {
        "gstr1":  gstr1_records,
        "gstr2b": gstr2b_records,
        "gstr3b": gstr3b_records,
    }


def generate_circular_trading_links(vendors: list[dict]) -> list[dict]:
    """
    Simulate a circular trading ring: V018 → V019 → V020 → V018
    In real fraud, money flows through shell companies to inflate ITC.
    Each link represents suspicious inter-vendor transactions.
    """
    ring = ["V018", "V019", "V020"]
    vendor_map = {v["vendor_id"]: v for v in vendors}
    links = []

    for i, from_id in enumerate(ring):
        to_id = ring[(i + 1) % len(ring)]
        from_v = vendor_map[from_id]
        to_v   = vendor_map[to_id]
        links.append({
            "from_vendor_id":   from_id,
            "to_vendor_id":     to_id,
            "from_gstin":       from_v["gstin"],
            "to_gstin":         to_v["gstin"],
            "from_name":        from_v["name"],
            "to_name":          to_v["name"],
            "transaction_count": random.randint(3, 8),
            "total_value":      random.randint(500_000, 2_000_000),
            "suspicious":       True,
        })

    return links


# ─── Master Data Store (singleton) ───────────────────────────
class MockDataStore:
    """
    In-memory knowledge graph store.
    This is the demo-mode fallback when Neo4j is not connected.

    Scalability note: In production, replace this with Neo4j queries.
    The graph structure here mirrors exactly what would exist in Neo4j,
    making the migration from mock → real a repository-layer swap only.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def initialize(self):
        if self._initialized:
            return
        self.taxpayer   = generate_taxpayer()
        self.vendors    = generate_vendors()
        self.invoices   = generate_invoices(self.vendors)
        returns         = generate_gstr_returns(self.vendors, self.invoices)
        self.gstr1      = returns["gstr1"]
        self.gstr2b     = returns["gstr2b"]
        self.gstr3b     = returns["gstr3b"]
        self.circular_links = generate_circular_trading_links(self.vendors)
        self._initialized = True
        print(f"[MockDataStore] Loaded: {len(self.vendors)} vendors, "
              f"{len(self.invoices)} invoices, {len(self.gstr1)} GSTR-1 records")

    def get_vendor_by_id(self, vendor_id: str) -> dict | None:
        return next((v for v in self.vendors if v["vendor_id"] == vendor_id), None)

    def get_invoice_by_id(self, invoice_id: str) -> dict | None:
        return next((i for i in self.invoices if i["invoice_id"] == invoice_id), None)

    def get_invoices_for_vendor(self, vendor_id: str) -> list[dict]:
        return [i for i in self.invoices if i["vendor_id"] == vendor_id]

    def get_dashboard_summary(self) -> dict:
        total_itc       = sum(i["total_gst"] for i in self.invoices)
        clean_itc       = sum(i["total_gst"] for i in self.invoices if i["risk_category"] == "LOW")
        medium_itc      = sum(i["total_gst"] for i in self.invoices if i["risk_category"] == "MEDIUM")
        high_itc        = sum(i["total_gst"] for i in self.invoices if i["risk_category"] == "HIGH")
        critical_itc    = sum(i["total_gst"] for i in self.invoices if i["risk_category"] == "CRITICAL")
        mismatched      = sum(1 for i in self.invoices if i["status"] == "MISMATCHED")
        matched         = sum(1 for i in self.invoices if i["status"] == "MATCHED")
        critical_vendors= sum(1 for v in self.vendors if v["risk_category"] == "CRITICAL")

        return {
            "total_invoices":     len(self.invoices),
            "total_vendors":      len(self.vendors),
            "total_itc_pool":     total_itc,
            "clean_itc":          clean_itc,
            "medium_risk_itc":    medium_itc,
            "high_risk_itc":      high_itc,
            "critical_itc":       critical_itc,
            "at_risk_itc":        high_itc + critical_itc,
            "matched_invoices":   matched,
            "mismatched_invoices":mismatched,
            "mismatch_pct":       round(mismatched / len(self.invoices) * 100, 1),
            "critical_vendors":   critical_vendors,
            "circular_trade_detected": True,
            "circular_trade_vendors":  3,
        }

    def get_risk_distribution(self) -> list[dict]:
        dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        for inv in self.invoices:
            dist[inv["risk_category"]] += 1
        return [{"category": k, "count": v} for k, v in dist.items()]

    def get_period_trend(self) -> list[dict]:
        trend = {}
        for inv in self.invoices:
            p = inv["period"]
            if p not in trend:
                trend[p] = {"period": p, "total": 0, "mismatched": 0, "itc": 0}
            trend[p]["total"] += 1
            trend[p]["itc"]   += inv["total_gst"]
            if inv["status"] == "MISMATCHED":
                trend[p]["mismatched"] += 1
        result = sorted(trend.values(), key=lambda x: x["period"])
        for r in result:
            r["mismatch_pct"] = round(r["mismatched"] / r["total"] * 100, 1) if r["total"] else 0
        return result


# Singleton instance — imported by all services
store = MockDataStore()
