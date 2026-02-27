import { inr } from './formatters';

export function generateAuditText(m) {
  if (!m) return 'Not found.';
  const ts = new Date().toLocaleString();
  const variance = m.gstr1_value - m.gstr2b_value;
  const pct = m.gstr1_value > 0 ? (Math.abs(variance) / m.gstr1_value * 100).toFixed(1) : 'N/A';
  const headers = {
    IRN_MISMATCH:               '⚠️  CRITICAL AUDIT FINDING — IRN INTEGRITY VIOLATION',
    AMOUNT_MISMATCH:            '   HIGH RISK FINDING — INVOICE VALUE DISCREPANCY',
    INVOICE_MISSING_2B:         '   HIGH RISK FINDING — INVOICE NOT IN GSTR-2B',
    EXTRA_IN_2B:                '   MEDIUM RISK FINDING — EXTRA INVOICE IN GSTR-2B',
    GSTIN_MISMATCH:             '   HIGH RISK FINDING — GSTIN IDENTIFIER MISMATCH',
    DATE_MISMATCH:              '   MEDIUM RISK FINDING — PERIOD DATE DISCREPANCY',
    EWAYBILL_MISSING:           '⚠️  CRITICAL FINDING — E-WAY BILL NOT GENERATED',
    PAYMENT_OVERDUE_180_DAYS:   '🔴  CRITICAL — SEC 16(2)(b) PAYMENT COMPLIANCE VIOLATION'
  };
  const rootCauses = {
    IRN_MISMATCH: `The Invoice Reference Number (IRN) could not be validated against\nthe IRP (Invoice Registration Portal). This indicates the IRN hash\nmay have been tampered with after generation. Under Rule 48(4) CGST\nRules, ITC on an invoice with invalid IRN is INADMISSIBLE.`,
    AMOUNT_MISMATCH: `Supplier filed an amendment (GSTR-1A) without buyer notification.\nThe amended value (${inr(m.gstr2b_value)}) differs from the original\ninvoice value (${inr(m.gstr1_value)}), creating a variance of ${inr(Math.abs(variance))} (${pct}%).`,
    INVOICE_MISSING_2B: `Supplier has not filed GSTR-1 for return period ${m.period}.\nAs per Section 16(2)(aa) CGST Act, ITC is only admissible when\nthe invoice appears in buyer's GSTR-2B. This invoice does NOT\nappear in auto-populated GSTR-2B. ITC MUST be deferred.`,
    EXTRA_IN_2B: `Supplier uploaded a duplicate invoice to GSTR-1. This invoice\nappears in GSTR-2B but has no corresponding purchase entry in\nthe buyer's records. Risk of phantom ITC claim.`,
    GSTIN_MISMATCH: `Incorrect GSTIN was captured at the point of purchase. The GSTIN\non the invoice does not match any registered supplier profile.\nITC under this invoice is inadmissible until rectification.`,
    DATE_MISMATCH: `Invoice was issued in period ${m.period} but supplier filed it in\na different GSTR-1 return period. This creates a time-of-supply\ndiscrepancy under Section 12/13 CGST Act.`,
    EWAYBILL_MISSING: `Goods valued above ₹50,000 were transported without a valid\nE-Way Bill as mandated by Rule 138 CGST Rules. This constitutes\na non-compliance event and ITC may be disallowed.`,
    PAYMENT_OVERDUE_180_DAYS: `Under Section 16(2)(b) CGST Act 2017, a buyer can avail ITC\nonly if payment (value + GST) is made to the supplier within\n180 days of the invoice date. This invoice has exceeded the\n180-day limit without confirmed payment. ITC already availed\nMUST be reversed with interest at 18% p.a. under Section 50(3).\nITC is re-claimable once payment is made (Rule 37(4)).`
  };
  const actions = {
    IRN_MISMATCH: `1. IMMEDIATELY reverse ITC of ${inr(m.itc_at_risk)} in current GSTR-3B\n2. Block payment to supplier until IRN validated\n3. File complaint on GST portal (Section 86A application)\n4. Preserve invoice + delivery challan as evidence\n5. Escalate to CFO and legal team within 24 hours`,
    AMOUNT_MISMATCH: `1. Issue formal notice to supplier requesting GSTR-1A amendment\n2. Provisionally reverse differential ITC of ${inr(m.itc_at_risk)}\n3. Monitor GSTR-2B for next 2 cycles for correction\n4. Reconcile TDS and accounts payable ledger`,
    INVOICE_MISSING_2B: `1. Verify supplier filing status on GST portal\n2. Defer ITC of ${inr(m.itc_at_risk)} until invoice reflects in GSTR-2B\n3. Issue formal demand notice to supplier\n4. Consider holding payments until GSTR-1 is filed`,
    EXTRA_IN_2B: `1. Do NOT avail ITC on this invoice\n2. Raise query with supplier for clarification\n3. Verify physical goods receipt against this invoice\n4. If confirmed duplicate, report to supplier`,
    GSTIN_MISMATCH: `1. Obtain correct GSTIN from supplier immediately\n2. Request supplier to file amended GSTR-1\n3. Do not avail ITC until corrected invoice received\n4. Update procurement records`,
    DATE_MISMATCH: `1. Reconcile invoice date against GSTR-2B period\n2. Adjust ITC claim to correct return period\n3. Verify no double-claiming across periods\n4. Coordinate with accounts payable team`,
    EWAYBILL_MISSING: `1. Obtain retrospective EWB if goods already received\n2. Reverse ITC of ${inr(m.itc_at_risk)} pending EWB validation\n3. Issue show-cause notice to logistics partner\n4. Update transport compliance policy`,
    PAYMENT_OVERDUE_180_DAYS: `1. REVERSE ITC of ${inr(m.itc_at_risk)} in GSTR-3B Table 4(B)(2) immediately\n2. Calculate interest: ${inr(m.itc_at_risk)} × 18% p.a. × days overdue ÷ 365\n3. Pay interest along with next GSTR-3B filing (Section 50(3))\n4. Make supplier payment immediately to stop interest accrual\n5. After payment: Re-claim ITC in GSTR-3B Table 4(A)(5) same month`
  };
  const type = m.mismatch_type;
  return `${headers[type] || 'AUDIT FINDING'}
${'═'.repeat(60)}
MISMATCH ID    : ${m.id}
INVOICE NO     : ${m.invoice_no}
SUPPLIER GSTIN : ${m.supplier_gstin}
RETURN PERIOD  : ${m.period}
DETECTION DATE : ${ts}
${'─'.repeat(60)}
SECTION 1 — OBSERVATION
${'─'.repeat(60)}
Mismatch Type  : ${type}
Root Cause     : ${m.root_cause}
GSTR-1 Value   : ${inr(m.gstr1_value)}
GSTR-2B Value  : ${inr(m.gstr2b_value)}
Variance       : ${inr(Math.abs(variance))} (${pct}%)
${'─'.repeat(60)}
SECTION 2 — ROOT CAUSE ANALYSIS
${'─'.repeat(60)}
${rootCauses[type] || 'See GST portal for details.'}
${'─'.repeat(60)}
SECTION 3 — ITC IMPACT
${'─'.repeat(60)}
ITC at Risk        : ${inr(m.itc_at_risk)}
Admissibility      : ${type === 'IRN_MISMATCH' ? 'INADMISSIBLE — Section 16(2)(aa)' : type === 'PAYMENT_OVERDUE_180_DAYS' ? 'REVERSAL MANDATORY — Section 16(2)(b)' : 'AT RISK — ITC deferral recommended'}
Disallowance Basis : ${type === 'PAYMENT_OVERDUE_180_DAYS' ? 'Section 16(2)(b) + Rule 37 CGST Act 2017 — Payment not made within 180 days' : 'Section 16(2)(c) / 16(2)(aa) CGST Act 2017'}${type === 'PAYMENT_OVERDUE_180_DAYS' ? `\nInterest Basis     : Section 50(3) @ 18% p.a. from date of ITC claim\nRe-claim Rule      : Rule 37(4) — ITC re-claimable in month of payment\nReport in          : GSTR-3B Table 4(B)(2) for reversal` : ''}
${'─'.repeat(60)}
SECTION 4 — RECOMMENDED ACTIONS
${'─'.repeat(60)}
${actions[type] || 'Contact GST helpdesk.'}
${'─'.repeat(60)}
SECTION 5 — RISK CLASSIFICATION
${'─'.repeat(60)}
Risk Level  : ${m.risk_level}  ${m.risk_level === 'CRITICAL' ? '⚠️  ESCALATE IMMEDIATELY TO CFO' : ''}
Status      : ${m.status}
Legal Refs  : ${type === 'PAYMENT_OVERDUE_180_DAYS' ? 'Section 16(2)(b), Rule 37, Section 50(3), GSTR-3B Table 4(B)(2), CBIC Circular 170/02/2022' : 'Section 16(2), Rule 36(4), Section 122(1)(ii) CGST Act'}
${'═'.repeat(60)}
Generated by GraphLedger AI Risk Engine v2.0
`;
}
