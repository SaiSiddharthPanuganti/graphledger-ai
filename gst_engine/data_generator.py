"""
Deliverable 2A — Mock Data Generator
======================================
Generates a realistic GST ecosystem simulation:

  50 Taxpayers  → across 6 Indian states
  500 Invoices  → B2B inter/intra-state, 5 GST rate slabs
  150 Mismatches→ 30% mismatch rate with weighted distribution
  50 Vendor Risk Profiles

Indian States covered:
  Delhi (07), Maharashtra (27), Gujarat (24),
  Tamil Nadu (33), Karnataka (29), Uttar Pradesh (09)

GST Rate Slabs: 0%, 5%, 12%, 18%, 28%
IGST = inter-state tax; CGST+SGST = intra-state tax (equal split)
IRN generated for invoices with taxable_value > ₹5,00,000
"""

import json
import random
import hashlib
import math
import os
from datetime import datetime, timedelta, date
from pathlib import Path

random.seed(2024)  # Reproducible

# ─── Constants ───────────────────────────────────────────────
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

STATES = {
    "07": "Delhi",        "27": "Maharashtra",
    "24": "Gujarat",      "33": "Tamil Nadu",
    "29": "Karnataka",    "09": "Uttar Pradesh",
}
STATE_CODES = list(STATES.keys())

SECTORS = ["Manufacturing", "Trading", "Services", "Export", "E-commerce"]
CATEGORIES = ["Regular", "Composition", "SEZ", "Regular", "Regular"]  # weighted
GST_RATES = [0, 5, 12, 18, 28]

PERIODS = [f"{m:02d}2024" for m in range(1, 13)]  # 012024 to 122024

MISMATCH_WEIGHTS = {
    "AMOUNT_MISMATCH":         0.30,
    "INVOICE_MISSING_2B":      0.22,
    "EXTRA_IN_2B":             0.09,
    "GSTIN_MISMATCH":          0.09,
    "DATE_MISMATCH":           0.09,
    "IRN_MISMATCH":            0.05,
    "EWAYBILL_MISSING":        0.05,
    "PAYMENT_OVERDUE_180_DAYS": 0.11,   # ~11% of mismatches are 180-day payment violations
}
MISMATCH_TYPES = list(MISMATCH_WEIGHTS.keys())
MISMATCH_PROBS = list(MISMATCH_WEIGHTS.values())

IRN_THRESHOLD = 500_000  # ₹5 lakh — e-invoice mandate threshold

COMPANY_PREFIXES = [
    "Tata", "Reliance", "Infosys", "Wipro", "Bajaj", "Mahindra", "Larsen",
    "Asian", "Havells", "Dixon", "Sundaram", "Minda", "Amara", "Exide",
    "Subros", "Allied", "Pioneer", "Sterling", "Apex", "Global", "National",
    "Prime", "Star", "Royal", "Supreme", "United", "Continental", "Premier",
    "Indian", "Modern", "Classic", "Century", "Horizon", "Zenith", "Alpha",
    "Beta", "Gamma", "Delta", "Sigma", "Omega", "Nova", "Vega", "Atlas",
    "Titan", "Bharat", "Hindustan", "Eastern", "Western", "Northern",
]
COMPANY_SUFFIXES = [
    "Industries Ltd", "Trading Co", "Pvt Ltd", "Exports Ltd",
    "Manufacturing", "Components Ltd", "Supplies", "Solutions",
]


def _pan(idx: int) -> str:
    """Generate deterministic PAN: AAXXX####X"""
    letters = "ABCDEFGHJKLMNPQRSTUVWXYZ"
    prefix = f"AA{letters[idx % 24]}{letters[(idx // 24) % 24]}{letters[(idx // 576) % 24]}"
    return f"{prefix}{(idx * 7 + 1000) % 9000 + 1000}{'ABCDEFGHJ'[idx % 9]}"


def _gstin(state_code: str, idx: int) -> str:
    """Generate realistic GSTIN."""
    pan = _pan(idx)
    check = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"[idx % 36]
    return f"{state_code}{pan}1Z{check}"


def _irn(supplier_gstin: str, invoice_no: str, inv_date: str) -> str:
    """Generate SHA-256 IRN hash."""
    payload = f"{supplier_gstin}|INV|{invoice_no}|{inv_date}"
    return hashlib.sha256(payload.encode()).hexdigest()


def _random_date_in_period(period: str) -> str:
    """Return a random date within MMYYYY period."""
    month = int(period[:2])
    year  = int(period[2:])
    max_day = 28 if month == 2 else 30 if month in [4, 6, 9, 11] else 31
    d = random.randint(1, max_day)
    return f"{year}-{month:02d}-{d:02d}"


def _compliance_score() -> float:
    """Gaussian-distributed compliance score, mean=75, std=15, clipped 20-98."""
    return max(20.0, min(98.0, random.gauss(75, 15)))


# ═══════════════════════════════════════════════════════════════
# GENERATORS
# ═══════════════════════════════════════════════════════════════

def generate_taxpayers(n: int = 50) -> list[dict]:
    taxpayers = []
    for i in range(n):
        state_code = STATE_CODES[i % len(STATE_CODES)]
        name = f"{random.choice(COMPANY_PREFIXES)} {random.choice(COMPANY_SUFFIXES)}"
        filing_streak = random.randint(0, 24)
        compliance    = round(_compliance_score(), 1)
        sector        = random.choice(SECTORS)
        category      = random.choices(CATEGORIES, weights=[5, 1, 1, 5, 2])[0]

        taxpayers.append({
            "taxpayer_id":       f"TP{i+1:03d}",
            "name":              name,
            "pan":               _pan(i),
            "gstin":             _gstin(state_code, i),
            "state_code":        state_code,
            "state":             STATES[state_code],
            "registration_date": f"20{random.randint(17, 22)}-{random.randint(1,12):02d}-01",
            "category":          category,
            "sector":            sector,
            "filing_frequency":  "Monthly" if category == "Regular" else "Quarterly",
            "annual_turnover":   round(random.uniform(50_00_000, 50_00_00_000), 2),
            "compliance_score":  compliance,
            "filing_streak":     filing_streak,
            "status":            "Active" if compliance > 30 else "Suspended",
        })
    return taxpayers


def generate_invoices(taxpayers: list[dict], n: int = 500) -> list[dict]:
    invoices = []
    tp_count = len(taxpayers)

    for i in range(n):
        # Pick supplier and buyer (different taxpayers)
        sup_idx = i % tp_count
        buy_idx = (i + random.randint(1, tp_count - 1)) % tp_count
        supplier = taxpayers[sup_idx]
        buyer    = taxpayers[buy_idx]

        period   = random.choice(PERIODS)
        inv_date = _random_date_in_period(period)
        gst_rate = random.choice(GST_RATES)

        # Amount distribution: mostly small, some large
        if random.random() < 0.6:
            taxable = round(random.uniform(10_000, 2_00_000), 2)
        elif random.random() < 0.8:
            taxable = round(random.uniform(2_00_000, 10_00_000), 2)
        else:
            taxable = round(random.uniform(10_00_000, 1_00_00_000), 2)

        tax_amt  = round(taxable * gst_rate / 100, 2)
        cess     = round(taxable * (0.01 if gst_rate == 28 else 0), 2)

        is_inter = supplier["state_code"] != buyer["state_code"]
        cgst = sgst = igst = 0.0
        if is_inter:
            igst = tax_amt
        else:
            cgst = sgst = round(tax_amt / 2, 2)

        total_value  = round(taxable + tax_amt + cess, 2)
        inv_no       = f"{supplier['taxpayer_id']}/2024/{i+1:05d}"

        # IRN for B2B invoices above threshold
        irn_number = None
        irn_status = None
        if taxable >= IRN_THRESHOLD:
            irn_number = _irn(supplier["gstin"], inv_no, inv_date)
            irn_status = random.choices(
                ["ACTIVE", "ACTIVE", "ACTIVE", "CANCELLED"],
                weights=[90, 5, 3, 2]
            )[0]

        # EWB for goods above ₹50,000 (assume all B2B are goods)
        ewb_no = None
        if taxable >= 50_000 and random.random() > 0.1:
            ewb_no = f"EWB{random.randint(100_000_000_000, 999_999_999_999)}"

        invoices.append({
            "invoice_id":     f"INV{i+1:05d}",
            "invoice_no":     inv_no,
            "invoice_date":   inv_date,
            "invoice_type":   "B2B",
            "supply_type":    "INTER_STATE" if is_inter else "INTRA_STATE",
            "return_period":  period,
            "supplier_id":    supplier["taxpayer_id"],
            "supplier_gstin": supplier["gstin"],
            "supplier_name":  supplier["name"],
            "buyer_id":       buyer["taxpayer_id"],
            "buyer_gstin":    buyer["gstin"],
            "buyer_name":     buyer["name"],
            "taxable_value":  taxable,
            "gst_rate":       gst_rate,
            "cgst":           cgst,
            "sgst":           sgst,
            "igst":           igst,
            "cess":           cess,
            "total_value":    total_value,
            "place_of_supply":buyer["state_code"],
            "irn":            irn_number,
            "irn_status":     irn_status,
            "ewb_no":         ewb_no,
        })
    return invoices


def generate_mismatches(invoices: list[dict], rate: float = 0.30) -> list[dict]:
    """
    Generate mismatches with weighted distribution:
      AMOUNT_MISMATCH    35%
      INVOICE_MISSING_2B 25%
      EXTRA_IN_2B        10%
      GSTIN_MISMATCH     10%
      DATE_MISMATCH      10%
      IRN_MISMATCH        5%
      EWAYBILL_MISSING    5%
    """
    n_mismatches  = int(len(invoices) * rate)
    mismatch_invs = random.sample(invoices, n_mismatches)
    mismatches    = []

    mtype_seq = random.choices(MISMATCH_TYPES, weights=MISMATCH_PROBS, k=n_mismatches)

    RISK_MAP = {
        "AMOUNT_MISMATCH":         ("HIGH",     1.0),
        "INVOICE_MISSING_2B":      ("HIGH",     1.2),
        "EXTRA_IN_2B":             ("MEDIUM",   0.5),
        "GSTIN_MISMATCH":          ("HIGH",     1.3),
        "DATE_MISMATCH":           ("MEDIUM",   0.8),
        "IRN_MISMATCH":            ("CRITICAL", 1.5),
        "EWAYBILL_MISSING":        ("MEDIUM",   0.6),
        "PAYMENT_OVERDUE_180_DAYS":("CRITICAL", 1.0),
    }

    ROOT_CAUSE_SHORT = {
        "AMOUNT_MISMATCH":    "Supplier filed GSTR-1A amendment post-GSTR-2B generation",
        "INVOICE_MISSING_2B": "Supplier did not file GSTR-1 for the return period",
        "EXTRA_IN_2B":        "Duplicate invoice uploaded by supplier in GSTR-1",
        "GSTIN_MISMATCH":     "Incorrect GSTIN provided at point of purchase",
        "DATE_MISMATCH":      "Invoice booked in Period T; reported in Period T+1",
        "IRN_MISMATCH":       "IRN cryptographic validation failed — possible tampering",
        "EWAYBILL_MISSING":   "Consignment above ₹50,000 without E-Way Bill",
        "PAYMENT_OVERDUE_180_DAYS": "Buyer has not paid supplier within 180 days of invoice date — Section 16(2)(b) ITC reversal triggered",
    }

    for i, (inv, mtype) in enumerate(zip(mismatch_invs, mtype_seq)):
        risk_level, multiplier = RISK_MAP[mtype]
        at_risk = round(inv["taxable_value"] * multiplier * random.uniform(0.05, 0.30), 2)

        # Simulated GSTR-1 vs 2B values for amount mismatch
        g1_val  = inv["taxable_value"]
        g2b_val = round(g1_val * random.uniform(0.75, 0.98), 2) if mtype == "AMOUNT_MISMATCH" else g1_val

        det_month = int(inv["return_period"][:2]) + 1
        det_year  = int(inv["return_period"][2:])
        if det_month > 12:
            det_month = 1
            det_year += 1
        detected_date = f"{det_year}-{det_month:02d}-14"

        mismatches.append({
            "mismatch_id":       f"MIS{i+1:04d}",
            "mismatch_type":     mtype,
            "invoice_id":        inv["invoice_id"],
            "invoice_no":        inv["invoice_no"],
            "supplier_gstin":    inv["supplier_gstin"],
            "supplier_name":     inv["supplier_name"],
            "buyer_gstin":       inv["buyer_gstin"],
            "return_period":     inv["return_period"],
            "detected_date":     detected_date,
            "gstr1_value":       g1_val,
            "gstr2b_value":      g2b_val,
            "amount_at_risk":    at_risk,
            "risk_level":        risk_level,
            "root_cause":        ROOT_CAUSE_SHORT[mtype],
            "resolution_status": random.choices(
                ["PENDING", "IN_PROGRESS", "RESOLVED"],
                weights=[60, 25, 15]
            )[0],
        })

    return mismatches


def generate_vendor_risk_profiles(taxpayers: list[dict], mismatches: list[dict]) -> list[dict]:
    """
    Compute composite vendor risk score for each taxpayer:
      composite = base_risk + mismatch_penalty + critical_penalty - filing_bonus
    Categories: CRITICAL (≥80), HIGH (≥60), MEDIUM (≥40), LOW (<40)
    """
    # Build mismatch index by supplier gstin
    mismatch_by_gstin: dict[str, list] = {}
    for m in mismatches:
        g = m["supplier_gstin"]
        mismatch_by_gstin.setdefault(g, []).append(m)

    profiles = []
    for tp in taxpayers:
        gstin   = tp["gstin"]
        g_mis   = mismatch_by_gstin.get(gstin, [])

        base_risk        = round(100 - tp["compliance_score"], 1)
        mismatch_penalty = min(30, len(g_mis) * 3)
        critical_penalty = sum(10 for m in g_mis if m["risk_level"] == "CRITICAL")
        filing_bonus     = min(20, tp["filing_streak"] * 1.5)

        composite = round(
            min(100, base_risk + mismatch_penalty + critical_penalty - filing_bonus),
            1
        )

        if composite >= 80:
            category = "CRITICAL"
        elif composite >= 60:
            category = "HIGH"
        elif composite >= 40:
            category = "MEDIUM"
        else:
            category = "LOW"

        total_at_risk = sum(m["amount_at_risk"] for m in g_mis)
        mtype_counts  = {}
        for m in g_mis:
            mtype_counts[m["mismatch_type"]] = mtype_counts.get(m["mismatch_type"], 0) + 1

        profiles.append({
            "vendor_id":       tp["taxpayer_id"],
            "gstin":           gstin,
            "name":            tp["name"],
            "state":           tp["state"],
            "sector":          tp["sector"],
            "filing_streak":   tp["filing_streak"],
            "compliance_score":tp["compliance_score"],
            "base_risk":       base_risk,
            "mismatch_penalty":mismatch_penalty,
            "critical_penalty":critical_penalty,
            "filing_bonus":    filing_bonus,
            "composite_risk_score": composite,
            "risk_category":   category,
            "mismatch_count":  len(g_mis),
            "total_itc_at_risk": total_at_risk,
            "mismatch_breakdown": mtype_counts,
        })

    return sorted(profiles, key=lambda x: x["composite_risk_score"], reverse=True)


def generate_payments(invoices: list[dict]) -> list[dict]:
    """
    Generate buyer-to-supplier payment records for invoices.

    Payment scenarios (reflecting real B2B credit market):
      40% — Paid on time (within 60 days): ITC safe
      25% — Paid late but within 180 days (60–180 days): ITC safe but slow
      20% — Paid AFTER 180 days: ITC was valid but must be reversed, then re-claimed
      15% — UNPAID (still outstanding): ITC reversal mandatory if 180 days have passed

    Section 16(2)(b) CGST Act:
      ITC reversal triggered when payment (value + tax) not made within 180 days.
      Interest at 18% p.a. accrues from date of original ITC claim.
      ITC re-claimable once payment is eventually made.
    """
    payments = []
    PAYMENT_MODES = ["NEFT", "RTGS", "CHEQUE", "UPI", "IMPS"]

    for inv in invoices:
        inv_date = datetime.strptime(inv["invoice_date"], "%Y-%m-%d")
        total_value = inv["total_value"]
        gst_value = inv["igst"] + inv["cgst"] + inv["sgst"]

        # Scenario weights: on_time, late_within_180, after_180, unpaid
        scenario = random.choices(
            ["on_time", "late_within_180", "after_180", "unpaid"],
            weights=[40, 25, 20, 15]
        )[0]

        if scenario == "unpaid":
            # No payment record — if invoice > 180 days old, ITC reversal required
            continue  # Absence of payment node signals the violation

        if scenario == "on_time":
            delay_days = random.randint(7, 60)
        elif scenario == "late_within_180":
            delay_days = random.randint(61, 179)
        else:  # after_180
            delay_days = random.randint(181, 365)

        pay_date = inv_date + timedelta(days=delay_days)

        payments.append({
            "payment_id":        f"PAY-{inv['invoice_id']}",
            "invoice_id":        inv["invoice_id"],
            "invoice_no":        inv["invoice_no"],
            "buyer_gstin":       inv["buyer_gstin"],
            "supplier_gstin":    inv["supplier_gstin"],
            "invoice_date":      inv["invoice_date"],
            "payment_date":      pay_date.strftime("%Y-%m-%d"),
            "amount_paid":       round(total_value, 2),
            "base_paid":         round(inv["taxable_value"], 2),
            "gst_paid":          round(gst_value, 2),
            "payment_mode":      random.choice(PAYMENT_MODES),
            "bank_ref":          f"UTR{random.randint(10**11, 10**12 - 1)}",
            "days_from_invoice": delay_days,
            "is_overdue":        delay_days > 180,
            "scenario":          scenario,
        })

    return payments


def generate_returns(taxpayers: list[dict], invoices: list[dict]) -> list[dict]:
    """Generate GSTR-1, GSTR-2B, GSTR-3B entries per taxpayer per period."""
    returns = []
    inv_by_supplier: dict = {}
    inv_by_buyer: dict    = {}
    for inv in invoices:
        inv_by_supplier.setdefault((inv["supplier_id"], inv["return_period"]), []).append(inv)
        inv_by_buyer.setdefault((inv["buyer_id"], inv["return_period"]), []).append(inv)

    for tp in taxpayers:
        for period in random.sample(PERIODS, random.randint(6, 12)):
            # GSTR-1 (sales return)
            sup_invs = inv_by_supplier.get((tp["taxpayer_id"], period), [])
            filed = random.random() < (tp["compliance_score"] / 100)
            m = int(period[:2])
            y = int(period[2:])
            nm = m + 1 if m < 12 else 1
            ny = y if m < 12 else y + 1
            due_date = f"{ny}-{nm:02d}-11"
            filed_date = None
            if filed:
                base = datetime.strptime(due_date, "%Y-%m-%d")
                filed_date = (base + timedelta(days=random.randint(0, 10))).strftime("%Y-%m-%d")

            total_liability = sum(i["igst"] + i["cgst"] + i["sgst"] for i in sup_invs)

            returns.append({
                "return_id":      f"RET-{tp['taxpayer_id']}-{period}-GSTR1",
                "gstin":          tp["gstin"],
                "return_period":  period,
                "return_type":    "GSTR1",
                "filed_date":     filed_date,
                "status":         "FILED" if filed else ("LATE" if random.random() > 0.5 else "PENDING"),
                "total_itc":      0,
                "total_liability":round(total_liability, 2),
                "invoice_count":  len(sup_invs),
            })

    return returns


# ═══════════════════════════════════════════════════════════════
# MAIN — Generate and save all data
# ═══════════════════════════════════════════════════════════════

def generate_all() -> dict:
    print("[*] Generating GST mock data...")

    taxpayers   = generate_taxpayers(50)
    invoices    = generate_invoices(taxpayers, 500)
    mismatches  = generate_mismatches(invoices, 0.30)
    vendors     = generate_vendor_risk_profiles(taxpayers, mismatches)
    returns_    = generate_returns(taxpayers, invoices)
    payments    = generate_payments(invoices)

    data = {
        "taxpayers":  taxpayers,
        "invoices":   invoices,
        "mismatches": mismatches,
        "vendors":    vendors,
        "returns":    returns_,
        "payments":   payments,
    }

    for key, records in data.items():
        path = DATA_DIR / f"{key}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, default=str)
        print(f"  [OK] {path.name}: {len(records)} records")

    print(f"\n[Summary]")
    print(f"  Taxpayers      : {len(taxpayers)}")
    print(f"  Invoices       : {len(invoices)}")
    print(f"  Mismatches     : {len(mismatches)} ({len(mismatches)/len(invoices)*100:.1f}% rate)")
    print(f"  Vendor Profiles: {len(vendors)}")
    print(f"  Returns        : {len(returns_)}")
    print(f"  Payments       : {len(payments)} ({len(payments)/len(invoices)*100:.1f}% invoices paid)")
    overdue = sum(1 for p in payments if p["is_overdue"])
    unpaid  = len(invoices) - len(payments)
    print(f"  Overdue (>180d): {overdue}")
    print(f"  Unpaid         : {unpaid}")

    type_dist = {}
    for m in mismatches:
        type_dist[m["mismatch_type"]] = type_dist.get(m["mismatch_type"], 0) + 1
    print(f"\n[Mismatch Distribution]")
    for mtype, cnt in sorted(type_dist.items(), key=lambda x: -x[1]):
        pct = cnt / len(mismatches) * 100
        print(f"  {mtype:<30} {cnt:>4} ({pct:5.1f}%)")

    return data


if __name__ == "__main__":
    generate_all()
