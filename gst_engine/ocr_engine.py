"""
GST Invoice OCR Engine
Extracts structured data from PDF invoices and validates against GSTR-2B
"""
import re
import json
import hashlib
from datetime import datetime
from pathlib import Path

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    import io
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

# ── GST regex patterns ──────────────────────────────────────────────
GSTIN_PATTERN = re.compile(r'\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b')
IRN_PATTERN   = re.compile(r'\b[0-9a-f]{64}\b', re.IGNORECASE)
INV_NO_PATTERN = re.compile(r'(?:Invoice\s*(?:No|Number|#)[.:\s]*|INV[-/]?)([A-Z0-9\-/]+)', re.IGNORECASE)
DATE_PATTERN  = re.compile(r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{2,4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\b', re.IGNORECASE)
AMOUNT_PATTERN = re.compile(r'(?:Rs\.?|₹|INR)?\s*([\d,]+(?:\.\d{2})?)', re.IGNORECASE)
CGST_PATTERN  = re.compile(r'CGST\s*(?:@\s*[\d.]+%)?\s*(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d{2})?)', re.IGNORECASE)
SGST_PATTERN  = re.compile(r'SGST\s*(?:@\s*[\d.]+%)?\s*(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d{2})?)', re.IGNORECASE)
IGST_PATTERN  = re.compile(r'IGST\s*(?:@\s*[\d.]+%)?\s*(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d{2})?)', re.IGNORECASE)
TAXABLE_PATTERN = re.compile(r'(?:Taxable\s*(?:Value|Amount)|Total\s*(?:before\s*tax|taxable))\s*(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d{2})?)', re.IGNORECASE)
TOTAL_PATTERN = re.compile(r'(?:Grand\s*Total|Total\s*Amount|Invoice\s*Total|Total)\s*(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d{2})?)', re.IGNORECASE)
EWB_PATTERN   = re.compile(r'(?:E-?Way\s*Bill\s*(?:No|Number)?[.:\s]*)(\d{12})', re.IGNORECASE)
PO_PATTERN    = re.compile(r'(?:PO\s*(?:No|Number)?[.:\s]*)([A-Z0-9\-/]+)', re.IGNORECASE)


def _clean_amount(s: str) -> float:
    """Convert '1,23,456.78' → 123456.78"""
    try:
        return float(str(s).replace(',', '').strip())
    except Exception:
        return 0.0


class InvoiceOCREngine:
    """
    Extracts structured GST invoice data from PDF or image files.
    Validates extracted data against GSTR-2B mock data.
    """

    def __init__(self, gstr2b_data: list = None):
        # Mock GSTR-2B data for validation (in real system loaded from DB)
        self.gstr2b_data = gstr2b_data or []
        self.history = []   # in-memory upload history

    # ── Public API ─────────────────────────────────────────────────

    def extract_from_pdf(self, file_bytes: bytes, filename: str = "invoice.pdf") -> dict:
        """Extract invoice fields from a PDF file (digital or scanned)."""
        text = ""
        pages_info = []

        if PDF_AVAILABLE:
            try:
                import io as _io
                with pdfplumber.open(_io.BytesIO(file_bytes)) as pdf:
                    for i, page in enumerate(pdf.pages):
                        page_text = page.extract_text() or ""
                        text += page_text + "\n"
                        pages_info.append({
                            "page": i + 1,
                            "chars": len(page_text),
                            "tables": len(page.extract_tables() or [])
                        })
            except Exception as e:
                text = f"PDF_ERROR: {e}"

        # Fallback to tesseract if pdfplumber got no text (scanned PDF)
        if len(text.strip()) < 50 and TESSERACT_AVAILABLE:
            try:
                from pdf2image import convert_from_bytes
                images = convert_from_bytes(file_bytes, dpi=200)
                for img in images:
                    text += pytesseract.image_to_string(img) + "\n"
            except Exception:
                pass

        return self._build_result(text, filename, pages_info, source="pdf")

    def extract_from_image(self, file_bytes: bytes, filename: str = "invoice.png") -> dict:
        """Extract invoice fields from an image (PNG/JPG)."""
        text = ""
        if TESSERACT_AVAILABLE:
            try:
                img = Image.open(io.BytesIO(file_bytes))
                text = pytesseract.image_to_string(img)
            except Exception as e:
                text = f"IMG_ERROR: {e}"
        else:
            text = "TESSERACT_NOT_INSTALLED"

        return self._build_result(text, filename, [], source="image")

    def extract_from_text(self, raw_text: str, filename: str = "pasted_text") -> dict:
        """Extract from pasted raw invoice text (for demo/testing)."""
        return self._build_result(raw_text, filename, [], source="text")

    # ── Core extraction ────────────────────────────────────────────

    def _build_result(self, text: str, filename: str, pages_info: list, source: str) -> dict:
        fields = self._extract_fields(text)
        mismatches = self.validate_against_gstr2b(fields)
        confidence = self._compute_confidence(fields)

        result = {
            "upload_id": f"OCR-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "filename": filename,
            "source": source,
            "extracted_at": datetime.now().isoformat(),
            "pages_info": pages_info,
            "raw_text_length": len(text),
            "fields": fields,
            "confidence": confidence,
            "overall_confidence": round(sum(confidence.values()) / len(confidence) * 100, 1) if confidence else 0,
            "mismatches_detected": mismatches,
            "mismatch_count": len(mismatches),
            "itc_at_risk": sum(m.get("itc_at_risk", 0) for m in mismatches),
            "validation_status": "CLEAN" if not mismatches else ("CRITICAL" if any(m["risk_level"] == "CRITICAL" for m in mismatches) else "FLAGGED"),
            "gstr2b_matched": any(m.get("source") == "gstr2b_match" for m in mismatches) if mismatches else False,
        }
        self.history.append(result)
        return result

    def _extract_fields(self, text: str) -> dict:
        """Run all regex extractors on the raw text."""
        gstins = GSTIN_PATTERN.findall(text)

        # Try to differentiate supplier vs buyer GSTIN by context
        supplier_gstin = ""
        buyer_gstin = ""
        if len(gstins) >= 2:
            # Heuristic: first GSTIN after "From/Supplier/Seller" is supplier
            supplier_match = re.search(r'(?:From|Supplier|Seller|Vendor)[^A-Z\d]*(' + GSTIN_PATTERN.pattern + r')', text, re.IGNORECASE)
            buyer_match    = re.search(r'(?:To|Buyer|Recipient|Bill\s*To)[^A-Z\d]*(' + GSTIN_PATTERN.pattern + r')', text, re.IGNORECASE)
            supplier_gstin = supplier_match.group(1) if supplier_match else gstins[0]
            buyer_gstin    = buyer_match.group(1) if buyer_match else gstins[1]
        elif len(gstins) == 1:
            supplier_gstin = gstins[0]

        irn_match = IRN_PATTERN.search(text)
        inv_match = INV_NO_PATTERN.search(text)
        date_matches = DATE_PATTERN.findall(text)
        ewb_match = EWB_PATTERN.search(text)
        po_match = PO_PATTERN.search(text)

        cgst   = _clean_amount(CGST_PATTERN.search(text).group(1)) if CGST_PATTERN.search(text) else 0.0
        sgst   = _clean_amount(SGST_PATTERN.search(text).group(1)) if SGST_PATTERN.search(text) else 0.0
        igst   = _clean_amount(IGST_PATTERN.search(text).group(1)) if IGST_PATTERN.search(text) else 0.0
        taxval = _clean_amount(TAXABLE_PATTERN.search(text).group(1)) if TAXABLE_PATTERN.search(text) else 0.0
        total  = _clean_amount(TOTAL_PATTERN.search(text).group(1)) if TOTAL_PATTERN.search(text) else 0.0

        # Infer supply type
        is_interstate = bool(supplier_gstin and buyer_gstin and supplier_gstin[:2] != buyer_gstin[:2])
        supply_type = "INTERSTATE" if is_interstate else ("INTRASTATE" if supplier_gstin else "UNKNOWN")
        if igst > 0:
            supply_type = "INTERSTATE"
        elif cgst > 0 or sgst > 0:
            supply_type = "INTRASTATE"

        # Guess GST rate
        tax_total = igst or (cgst + sgst)
        gst_rate = 0
        if taxval > 0 and tax_total > 0:
            rate = round((tax_total / taxval) * 100)
            for valid in [5, 12, 18, 28]:
                if abs(rate - valid) <= 2:
                    gst_rate = valid
                    break

        return {
            "invoice_no":      inv_match.group(1).strip() if inv_match else "",
            "invoice_date":    date_matches[0] if date_matches else "",
            "supplier_gstin":  supplier_gstin,
            "buyer_gstin":     buyer_gstin,
            "all_gstins":      list(set(gstins)),
            "irn":             irn_match.group(0) if irn_match else "",
            "eway_bill_no":    ewb_match.group(1) if ewb_match else "",
            "po_number":       po_match.group(1) if po_match else "",
            "taxable_value":   taxval,
            "cgst":            cgst,
            "sgst":            sgst,
            "igst":            igst,
            "total_tax":       tax_total,
            "total_value":     total or (taxval + tax_total),
            "gst_rate":        gst_rate,
            "supply_type":     supply_type,
            "irn_required":    taxval >= 500000,   # IRN mandatory above ₹5L
            "ewb_required":    taxval >= 50000,    # EWB mandatory above ₹50k
        }

    def _compute_confidence(self, fields: dict) -> dict:
        """Confidence score per field (0-1) based on extraction quality."""
        scores = {}
        scores["invoice_no"]     = 0.9 if fields.get("invoice_no") else 0.0
        scores["invoice_date"]   = 0.9 if fields.get("invoice_date") else 0.0
        scores["supplier_gstin"] = 1.0 if re.match(r'^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$', fields.get("supplier_gstin", "")) else 0.0
        scores["buyer_gstin"]    = 1.0 if re.match(r'^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$', fields.get("buyer_gstin", "")) else 0.0
        scores["taxable_value"]  = 0.95 if fields.get("taxable_value", 0) > 0 else 0.0
        scores["total_tax"]      = 0.95 if fields.get("total_tax", 0) > 0 else 0.0
        scores["irn"]            = 1.0 if len(fields.get("irn", "")) == 64 else 0.0
        scores["eway_bill"]      = 1.0 if len(fields.get("eway_bill_no", "")) == 12 else 0.0
        return scores

    # ── GSTR-2B Validation ────────────────────────────────────────

    def validate_against_gstr2b(self, fields: dict) -> list:
        """
        Compare extracted invoice fields against GSTR-2B records.
        Returns list of detected mismatches with risk classification.
        """
        mismatches = []
        inv_no = fields.get("invoice_no", "")
        supplier = fields.get("supplier_gstin", "")
        taxval = fields.get("taxable_value", 0)
        irn = fields.get("irn", "")
        ewb = fields.get("eway_bill_no", "")

        # Find matching record in GSTR-2B
        gstr2b_record = None
        for rec in self.gstr2b_data:
            if rec.get("invoice_no") == inv_no or rec.get("supplier_gstin") == supplier:
                gstr2b_record = rec
                break

        # Rule 1: IRN required but missing
        if fields.get("irn_required") and not irn:
            mismatches.append({
                "mismatch_type": "IRN_MISMATCH",
                "risk_level": "CRITICAL",
                "description": f"Invoice value ₹{taxval:,.0f} exceeds ₹5L threshold — IRN mandatory under Rule 48(4)",
                "itc_at_risk": taxval * 0.18,
                "legal_ref": "Rule 48(4) CGST Rules 2017",
                "action": "Obtain valid IRN from IRP portal before claiming ITC"
            })

        # Rule 2: EWB required but missing
        if fields.get("ewb_required") and not ewb:
            mismatches.append({
                "mismatch_type": "EWAYBILL_MISSING",
                "risk_level": "CRITICAL",
                "description": f"Goods value ₹{taxval:,.0f} exceeds ₹50k — E-Way Bill mandatory under Rule 138",
                "itc_at_risk": taxval * 0.18,
                "legal_ref": "Rule 138 CGST Rules 2017",
                "action": "Generate E-Way Bill before goods movement or obtain retrospective EWB"
            })

        # Rule 3: GSTIN format validation
        gstin_re = re.compile(r'^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$')
        if supplier and not gstin_re.match(supplier):
            mismatches.append({
                "mismatch_type": "GSTIN_MISMATCH",
                "risk_level": "HIGH",
                "description": f"Supplier GSTIN '{supplier}' fails checksum validation",
                "itc_at_risk": taxval * 0.18,
                "legal_ref": "Section 16(2)(a) CGST Act",
                "action": "Verify GSTIN with supplier and obtain corrected invoice"
            })

        # Rule 4: Compare with GSTR-2B if record found
        if gstr2b_record:
            gstr2b_val = gstr2b_record.get("taxable_value", 0)
            if gstr2b_val > 0 and taxval > 0:
                variance_pct = abs(taxval - gstr2b_val) / gstr2b_val * 100
                if variance_pct > 2:
                    diff = abs(taxval - gstr2b_val)
                    mismatches.append({
                        "mismatch_type": "AMOUNT_MISMATCH",
                        "risk_level": "HIGH" if variance_pct > 10 else "MEDIUM",
                        "description": f"Invoice value ₹{taxval:,.0f} differs from GSTR-2B value ₹{gstr2b_val:,.0f} by {variance_pct:.1f}%",
                        "gstr1_value": taxval,
                        "gstr2b_value": gstr2b_val,
                        "variance": diff,
                        "variance_pct": round(variance_pct, 1),
                        "itc_at_risk": diff * 0.18,
                        "legal_ref": "Rule 36(4) CGST Rules — 105% GSTR-2B cap",
                        "action": "Contact supplier to file amendment in GSTR-1A",
                        "source": "gstr2b_match"
                    })
        else:
            # Invoice not found in GSTR-2B
            if supplier and inv_no:
                mismatches.append({
                    "mismatch_type": "INVOICE_MISSING_2B",
                    "risk_level": "HIGH",
                    "description": f"Invoice {inv_no} from {supplier} not found in GSTR-2B — ITC cannot be claimed",
                    "itc_at_risk": taxval * 0.18,
                    "legal_ref": "Section 16(2)(aa) CGST Act",
                    "action": "Verify supplier GSTR-1 filing status. Defer ITC until invoice appears in GSTR-2B"
                })

        return mismatches

    def get_history(self) -> list:
        return list(reversed(self.history))

    def get_summary_stats(self) -> dict:
        total = len(self.history)
        clean = sum(1 for h in self.history if h["validation_status"] == "CLEAN")
        critical = sum(1 for h in self.history if h["validation_status"] == "CRITICAL")
        total_itc_risk = sum(h.get("itc_at_risk", 0) for h in self.history)
        return {
            "total_uploaded": total,
            "clean": clean,
            "flagged": total - clean - critical,
            "critical": critical,
            "total_itc_at_risk": round(total_itc_risk, 2),
            "avg_confidence": round(sum(h.get("overall_confidence", 0) for h in self.history) / max(1, total), 1)
        }


# ── CLI test ────────────────────────────────────────────────────────
if __name__ == "__main__":
    engine = InvoiceOCREngine()

    # Test with raw invoice text
    sample_text = """
    TAX INVOICE
    Invoice No: INV-2024-1042
    Invoice Date: 15-Oct-2024

    From (Supplier):
    Mahindra Castings Pvt Ltd
    GSTIN: 27AABCM1234F1Z5
    Plot 42, MIDC, Pune - 411019

    To (Recipient):
    ACME Exports Limited
    GSTIN: 29AADCV5678B1ZP
    Electronic City, Bangalore - 560100

    IRN: a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2

    Description          HSN     Qty    Rate      Amount
    Steel Castings       7325    500    850.00    4,25,000.00
    Machined Parts       8483    200    1,200.00  2,40,000.00
                                       Taxable   6,65,000.00
                                       IGST 18%  1,19,700.00
                                       Total     7,84,700.00

    E-Way Bill No: 321456789012
    PO No: PO-ACME-2024-089
    """
    result = engine.extract_from_text(sample_text, "sample_invoice.txt")
    print("=== EXTRACTION RESULT ===")
    print(json.dumps(result, indent=2, default=str))
    print(f"\nOverall Confidence: {result['overall_confidence']}%")
    print(f"Mismatches Detected: {result['mismatch_count']}")
    print(f"Validation Status: {result['validation_status']}")
