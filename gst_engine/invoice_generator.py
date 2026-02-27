"""
GST Invoice PDF Generator
Creates realistic sample GST invoices for OCR testing
"""
import hashlib, random, json
from datetime import datetime, timedelta
from pathlib import Path

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Sample supplier/buyer pairs matching the dashboard data
SUPPLIERS = [
    {"name": "Mahindra Castings Pvt Ltd",   "gstin": "27AABCM1234F1Z5", "address": "Plot 42, MIDC Bhosari, Pune - 411026, Maharashtra",   "state": "27"},
    {"name": "Flex Systems India Ltd",       "gstin": "07AAFCS9876K1Z3", "address": "Unit 5, Okhla Phase II, New Delhi - 110020",          "state": "07"},
    {"name": "Gujarat Agro Chemicals Ltd",   "gstin": "24AAACG8765H1Z7", "address": "GIDC Estate, Ankleshwar, Bharuch - 393002, Gujarat",  "state": "24"},
    {"name": "Chennai Electrical Co",        "gstin": "33AAECS3456J1Z1", "address": "Anna Nagar West, Chennai - 600040, Tamil Nadu",       "state": "33"},
    {"name": "Jain Logistics UP",            "gstin": "09AAACJ6543M1Z9", "address": "Transport Nagar, Lucknow - 226023, Uttar Pradesh",    "state": "09"},
    {"name": "Bangalore Auto Parts",         "gstin": "29AAACG2345N1Z2", "address": "Peenya Industrial Area, Bangalore - 560058, Karnataka","state": "29"},
]

BUYER = {"name": "ACME Exports Limited", "gstin": "29AADCV5678B1ZP",
         "address": "Electronic City Phase 1, Bangalore - 560100, Karnataka"}

HSN_ITEMS = {
    "Manufacturing": [("Steel Castings", "7325"), ("Machined Parts", "8483"), ("Forged Components", "7326")],
    "Services":      [("IT Services", "9983"), ("Consulting", "9983"), ("Cloud Hosting", "9984")],
    "Trading":       [("Electrical Equipment", "8543"), ("Control Panels", "8537"), ("Cables", "8544")],
    "Logistics":     [("Transport Services", "9965"), ("Warehousing", "9967"), ("Freight", "9965")],
    "Chemicals":     [("Agro Chemicals", "3808"), ("Fertilizers", "3102"), ("Pesticides", "3808")],
    "Auto Parts":    [("Engine Parts", "8409"), ("Brake Assemblies", "8708"), ("Filters", "8421")],
}

SECTORS = ["Manufacturing", "Services", "Trading", "Logistics", "Chemicals", "Auto Parts"]

def generate_irn(invoice_no: str, gstin: str, date: str) -> str:
    payload = f"{gstin}|{invoice_no}|{date}"
    return hashlib.sha256(payload.encode()).hexdigest()

def generate_ewb_no() -> str:
    return str(random.randint(100000000000, 999999999999))

def indian_format(n: float) -> str:
    """Format number as Indian numbering: 1,23,456.00"""
    n = round(n, 2)
    s = f"{n:.2f}"
    integer_part, decimal_part = s.split(".")
    result = []
    for i, d in enumerate(reversed(integer_part)):
        if i == 3 or (i > 3 and (i - 3) % 2 == 0):
            result.append(",")
        result.append(d)
    return "".join(reversed(result)) + "." + decimal_part


def generate_invoice_data(supplier_idx: int = 0, scenario: str = "clean") -> dict:
    """
    Generate synthetic invoice data.
    scenario: 'clean' | 'missing_irn' | 'missing_ewb' | 'amount_mismatch' | 'wrong_gstin'
    """
    supplier = SUPPLIERS[supplier_idx % len(SUPPLIERS)]
    sector = SECTORS[supplier_idx % len(SECTORS)]
    items_pool = HSN_ITEMS.get(sector, HSN_ITEMS["Manufacturing"])

    base_date = datetime(2024, 10, 15)
    invoice_date = base_date + timedelta(days=random.randint(-30, 30))
    inv_suffix = random.randint(1000, 9999)
    invoice_no = f"INV-{invoice_date.year}-{inv_suffix}"

    # Generate line items
    n_items = random.randint(2, 4)
    line_items = []
    for i in range(n_items):
        item_name, hsn = random.choice(items_pool)
        qty = random.randint(50, 500)
        rate = random.choice([500, 750, 850, 1000, 1200, 1500, 2000])
        amount = qty * rate
        line_items.append({"desc": item_name, "hsn": hsn, "qty": qty, "rate": rate, "amount": amount})

    taxable_value = sum(i["amount"] for i in line_items)

    # Interstate = IGST, Intrastate = CGST+SGST
    is_interstate = supplier["state"] != "29"
    gst_rate = random.choice([5, 12, 18, 28])
    tax_amount = round(taxable_value * gst_rate / 100, 2)

    if is_interstate:
        cgst, sgst, igst = 0, 0, tax_amount
    else:
        cgst = sgst = round(tax_amount / 2, 2)
        igst = 0

    total = taxable_value + tax_amount
    irn = generate_irn(invoice_no, supplier["gstin"], invoice_date.strftime("%d/%m/%Y"))
    ewb_no = generate_ewb_no() if taxable_value >= 50000 else ""

    # Apply scenario mutations
    if scenario == "missing_irn" and taxable_value >= 500000:
        irn = ""
    elif scenario == "missing_ewb":
        ewb_no = ""
    elif scenario == "wrong_gstin":
        gstin_list = list(supplier["gstin"])
        gstin_list[5] = "X"
        supplier = {**supplier, "gstin": "".join(gstin_list)}
    elif scenario == "amount_mismatch":
        taxable_value = round(taxable_value * 0.85, 2)  # 15% less than filed

    po_no = f"PO-ACME-{invoice_date.year}-{random.randint(100, 999)}"

    return {
        "invoice_no": invoice_no,
        "invoice_date": invoice_date.strftime("%d-%b-%Y"),
        "supplier": supplier,
        "buyer": BUYER,
        "line_items": line_items,
        "taxable_value": taxable_value,
        "cgst": cgst,
        "sgst": sgst,
        "igst": igst,
        "gst_rate": gst_rate,
        "total": total,
        "irn": irn,
        "eway_bill_no": ewb_no,
        "po_no": po_no,
        "supply_type": "INTERSTATE" if is_interstate else "INTRASTATE",
        "scenario": scenario,
    }


def generate_pdf(data: dict, output_path: str) -> bool:
    if not REPORTLAB_AVAILABLE:
        print("reportlab not installed. Run: pip install reportlab")
        return False

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            rightMargin=15*mm, leftMargin=15*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    W = A4[0] - 30*mm

    title_style  = ParagraphStyle("title",  parent=styles["Normal"], fontSize=16, fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=4)
    head_style   = ParagraphStyle("head",   parent=styles["Normal"], fontSize=9,  fontName="Helvetica-Bold")
    small_style  = ParagraphStyle("small",  parent=styles["Normal"], fontSize=8,  fontName="Helvetica")
    right_style  = ParagraphStyle("right",  parent=styles["Normal"], fontSize=9,  alignment=TA_RIGHT)

    elements = []

    # ── Header ──
    elements.append(Paragraph("TAX INVOICE", title_style))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.darkblue))
    elements.append(Spacer(1, 4*mm))

    inv_info = [
        [Paragraph(f"<b>Invoice No:</b> {data['invoice_no']}", small_style),
         Paragraph(f"<b>Date:</b> {data['invoice_date']}", small_style)],
        [Paragraph(f"<b>Supply Type:</b> {data['supply_type']}", small_style),
         Paragraph(f"<b>PO No:</b> {data['po_no']}", small_style)],
    ]
    t = Table(inv_info, colWidths=[W*0.5, W*0.5])
    t.setStyle(TableStyle([("GRID", (0,0), (-1,-1), 0.5, colors.lightgrey),
                            ("PADDING", (0,0), (-1,-1), 5)]))
    elements.append(t)
    elements.append(Spacer(1, 4*mm))

    # ── Supplier / Buyer ──
    party_data = [
        [Paragraph("<b>Supplier (From)</b>", head_style),
         Paragraph("<b>Recipient (To)</b>", head_style)],
        [Paragraph(f"<b>{data['supplier']['name']}</b><br/>"
                   f"GSTIN: {data['supplier']['gstin']}<br/>"
                   f"{data['supplier']['address']}", small_style),
         Paragraph(f"<b>{data['buyer']['name']}</b><br/>"
                   f"GSTIN: {data['buyer']['gstin']}<br/>"
                   f"{data['buyer']['address']}", small_style)],
    ]
    t = Table(party_data, colWidths=[W*0.5, W*0.5])
    t.setStyle(TableStyle([("GRID",       (0,0), (-1,-1), 0.5, colors.lightgrey),
                            ("BACKGROUND", (0,0), (-1,0),  colors.Color(0.9, 0.9, 1)),
                            ("PADDING",    (0,0), (-1,-1), 6)]))
    elements.append(t)
    elements.append(Spacer(1, 4*mm))

    # ── Line Items ──
    item_header = [["#", "Description", "HSN/SAC", "Qty", "Rate (₹)", "Amount (₹)"]]
    item_rows = [[str(i+1), it["desc"], it["hsn"], str(it["qty"]),
                  indian_format(it["rate"]), indian_format(it["amount"])]
                 for i, it in enumerate(data["line_items"])]
    item_data = item_header + item_rows

    t = Table(item_data, colWidths=[W*0.05, W*0.32, W*0.12, W*0.10, W*0.18, W*0.23])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.Color(0.1, 0.1, 0.4)),
        ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 8),
        ("GRID",       (0,0), (-1,-1), 0.5, colors.lightgrey),
        ("ALIGN",      (3,1), (-1,-1), "RIGHT"),
        ("PADDING",    (0,0), (-1,-1), 5),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.Color(0.97, 0.97, 1)]),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 2*mm))

    # ── Tax Summary ──
    tax_rows = [[Paragraph("<b>Taxable Value</b>", small_style),
                 Paragraph(f"₹ {indian_format(data['taxable_value'])}", right_style)]]
    if data["cgst"]:
        tax_rows.append([Paragraph(f"CGST @ {data['gst_rate']//2}%", small_style),
                         Paragraph(f"₹ {indian_format(data['cgst'])}", right_style)])
        tax_rows.append([Paragraph(f"SGST @ {data['gst_rate']//2}%", small_style),
                         Paragraph(f"₹ {indian_format(data['sgst'])}", right_style)])
    if data["igst"]:
        tax_rows.append([Paragraph(f"IGST @ {data['gst_rate']}%", small_style),
                         Paragraph(f"₹ {indian_format(data['igst'])}", right_style)])
    tax_rows.append([Paragraph("<b>Grand Total</b>", head_style),
                     Paragraph(f"<b>₹ {indian_format(data['total'])}</b>", right_style)])

    t = Table(tax_rows, colWidths=[W*0.75, W*0.25])
    t.setStyle(TableStyle([
        ("GRID",       (0,0), (-1,-1), 0.5, colors.lightgrey),
        ("BACKGROUND", (0,-1), (-1,-1), colors.Color(0.9, 1, 0.9)),
        ("PADDING",    (0,0), (-1,-1), 5),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 4*mm))

    # ── IRN / EWB ──
    footer_rows = []
    if data.get("irn"):
        footer_rows.append([Paragraph("<b>IRN:</b>", head_style),
                             Paragraph(f"<font name='Courier' size='7'>{data['irn']}</font>", small_style)])
    else:
        footer_rows.append([Paragraph("<b>IRN:</b>", head_style),
                             Paragraph("<font color='red'>NOT GENERATED</font>", small_style)])
    if data.get("eway_bill_no"):
        footer_rows.append([Paragraph("<b>E-Way Bill No:</b>", head_style),
                             Paragraph(data["eway_bill_no"], small_style)])
    else:
        footer_rows.append([Paragraph("<b>E-Way Bill No:</b>", head_style),
                             Paragraph("<font color='red'>NOT APPLICABLE / MISSING</font>", small_style)])

    if footer_rows:
        t = Table(footer_rows, colWidths=[W*0.20, W*0.80])
        t.setStyle(TableStyle([("GRID",    (0,0), (-1,-1), 0.5, colors.lightgrey),
                                ("PADDING", (0,0), (-1,-1), 5),
                                ("BACKGROUND", (0,0), (-1,-1), colors.Color(0.97, 0.97, 0.97))]))
        elements.append(t)

    elements.append(Spacer(1, 6*mm))
    elements.append(Paragraph("This is a computer-generated invoice. No signature required. "
                               "Subject to jurisdiction of Bangalore courts.",
                               ParagraphStyle("footer", parent=styles["Normal"], fontSize=7,
                                              textColor=colors.grey, alignment=TA_CENTER)))

    doc.build(elements)
    return True


def generate_sample_invoices(output_dir: str = "sample_invoices") -> list:
    """Generate one invoice per scenario for testing."""
    out = Path(output_dir)
    out.mkdir(exist_ok=True)

    scenarios = [
        (0, "clean",          "01_clean_interstate_invoice.pdf"),
        (1, "clean",          "02_clean_intrastate_invoice.pdf"),
        (2, "missing_irn",    "03_CRITICAL_missing_irn.pdf"),
        (3, "missing_ewb",    "04_CRITICAL_missing_ewb.pdf"),
        (4, "amount_mismatch","05_HIGH_amount_mismatch.pdf"),
        (5, "wrong_gstin",    "06_HIGH_wrong_gstin.pdf"),
    ]

    generated = []
    for idx, scenario, filename in scenarios:
        data = generate_invoice_data(idx, scenario)
        path = out / filename
        ok = generate_pdf(data, str(path))
        status = "OK" if ok else "FAILED"
        print(f"  [{status}] {filename}")
        generated.append({"file": filename, "scenario": scenario, "status": status, "data": data})

    return generated


if __name__ == "__main__":
    print("Generating sample GST invoices...")
    results = generate_sample_invoices("sample_invoices")
    print(f"\nGenerated {len(results)} invoices in ./sample_invoices/")
    for r in results:
        d = r["data"]
        print(f"  {r['file']}: ₹{d['total']:,.0f} | {d['supply_type']} | IRN={'YES' if d['irn'] else 'NO'} | EWB={'YES' if d['eway_bill_no'] else 'NO'}")
