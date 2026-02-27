// ============================================================
// GraphLedger AI — Neo4j Knowledge Graph Schema
// GST ITC Reconciliation Engine
// ============================================================
// GST PRIMER (for developers new to GST):
//   GSTIN   = Goods & Services Tax Identification Number (15-char)
//   ITC     = Input Tax Credit (tax paid on purchases, claimable)
//   GSTR-1  = Monthly sales return filed by VENDOR (seller)
//   GSTR-2B = Auto-populated purchase statement for BUYER
//   GSTR-3B = Summary return + ITC claim filed by BUYER
//   IRN     = Invoice Reference Number (e-invoice mandate)
// ============================================================

// ─── CONSTRAINTS (Uniqueness + Index) ────────────────────────
CREATE CONSTRAINT taxpayer_gstin IF NOT EXISTS
  FOR (t:Taxpayer) REQUIRE t.gstin IS UNIQUE;

CREATE CONSTRAINT vendor_gstin IF NOT EXISTS
  FOR (v:Vendor) REQUIRE v.gstin IS UNIQUE;

CREATE CONSTRAINT invoice_id IF NOT EXISTS
  FOR (i:Invoice) REQUIRE i.invoice_id IS UNIQUE;

CREATE CONSTRAINT irn_number IF NOT EXISTS
  FOR (r:IRN) REQUIRE r.irn_number IS UNIQUE;

CREATE CONSTRAINT gstr1_id IF NOT EXISTS
  FOR (g:GSTR1) REQUIRE g.gstr1_id IS UNIQUE;

CREATE CONSTRAINT gstr2b_id IF NOT EXISTS
  FOR (g:GSTR2B) REQUIRE g.gstr2b_id IS UNIQUE;

CREATE CONSTRAINT gstr3b_id IF NOT EXISTS
  FOR (g:GSTR3B) REQUIRE g.gstr3b_id IS UNIQUE;

CREATE CONSTRAINT payment_id IF NOT EXISTS
  FOR (p:Payment) REQUIRE p.payment_id IS UNIQUE;

// ─── NODE INDEXES (Performance for graph traversal) ──────────
CREATE INDEX invoice_status IF NOT EXISTS FOR (i:Invoice) ON (i.status);
CREATE INDEX invoice_risk    IF NOT EXISTS FOR (i:Invoice) ON (i.risk_category);
CREATE INDEX vendor_score    IF NOT EXISTS FOR (v:Vendor)  ON (v.compliance_score);

// ============================================================
// NODE DEFINITIONS WITH PROPERTY CONTRACTS
// ============================================================

// Taxpayer: The company claiming ITC (Input Tax Credit)
// MERGE (t:Taxpayer {
//   gstin: "27AABCM1234A1Z5",          // 15-char GST ID
//   name: "Mahindra Auto Parts Ltd",
//   state_code: "27",
//   state: "Maharashtra",
//   pan: "AABCM1234A",                 // Permanent Account Number
//   annual_turnover: 150000000,        // in INR
//   registration_date: date("2017-07-01"),
//   taxpayer_type: "Regular"           // Regular / Composition / SEZ
// })

// Vendor: The seller (supplier) of goods/services
// MERGE (v:Vendor {
//   gstin: "29AADCV5678B1ZP",
//   name: "TechSupplies Pvt Ltd",
//   state_code: "29",
//   state: "Karnataka",
//   compliance_score: 0.85,            // 0.0 (worst) to 1.0 (best)
//   filing_frequency: "Monthly",       // Monthly / Quarterly
//   last_filed_period: "2024-11",
//   total_invoices: 45,
//   valid_invoice_pct: 0.91,
//   risk_category: "LOW"               // LOW / MEDIUM / HIGH / CRITICAL
// })

// Invoice: A B2B tax invoice (triggers ITC claim)
// MERGE (i:Invoice {
//   invoice_id: "INV-001",
//   invoice_number: "TEC/2024/001",
//   invoice_date: date("2024-10-15"),
//   taxable_amount: 100000,            // base amount in INR
//   cgst: 9000,                        // Central GST (9%)
//   sgst: 9000,                        // State GST (9%)
//   igst: 0,                           // Integrated GST (for inter-state)
//   total_gst: 18000,
//   total_amount: 118000,
//   period: "2024-10",                 // Tax period (YYYY-MM)
//   status: "MATCHED",                 // MATCHED / MISMATCHED / MISSING / PENDING
//   risk_score: 15,                    // 0-100 computed risk score
//   risk_category: "LOW",
//   mismatch_reason: null,
//   irn_valid: true,
//   in_gstr2b: true,
//   vendor_filed: true,
//   tax_paid: true
// })

// IRN: E-Invoice Reference Number (mandatory for B2B > ₹5Cr turnover)
// MERGE (r:IRN {
//   irn_number: "a5c3f...(64-char hash)",
//   generated_at: datetime("2024-10-15T10:30:00"),
//   valid: true,
//   cancelled: false,
//   cancel_date: null,
//   qr_code_hash: "hash..."
// })

// GSTR1: Sales return filed by VENDOR — lists all invoices issued
// MERGE (g:GSTR1 {
//   gstr1_id: "GSTR1-V001-2024-10",
//   vendor_gstin: "29AADCV5678B1ZP",
//   period: "2024-10",
//   filing_date: date("2024-11-11"),   // Due date is 11th of next month
//   filed: true,
//   invoice_count: 12,
//   total_tax_value: 216000
// })

// GSTR2B: Auto-drafted purchase register for BUYER (read-only, system-generated)
// MERGE (g:GSTR2B {
//   gstr2b_id: "GSTR2B-BUYER-2024-10",
//   period: "2024-10",
//   generated_date: date("2024-11-14"),
//   invoice_count: 87,
//   total_itc_available: 1566000
// })

// GSTR3B: Summary return filed by BUYER — claims ITC
// MERGE (g:GSTR3B {
//   gstr3b_id: "GSTR3B-BUYER-2024-10",
//   period: "2024-10",
//   filing_date: date("2024-11-20"),   // Due date is 20th of next month
//   filed: true,
//   itc_claimed: 1490000,
//   tax_paid: 340000,
//   late_fee: 0
// })

// Payment: Tax payment challan (proof of tax deposit)
// MERGE (p:Payment {
//   payment_id: "PMT-2024-10-001",
//   challan_number: "CIN20241101XXXX",
//   amount: 340000,
//   payment_date: date("2024-11-20"),
//   bank: "HDFC Bank",
//   status: "SUCCESS"
// })

// ============================================================
// RELATIONSHIP DEFINITIONS
// ============================================================

// (Taxpayer)-[:PURCHASED]->(Invoice)
//   The taxpayer bought goods/services documented in this invoice

// (Invoice)-[:ISSUED_BY]->(Vendor)
//   The vendor issued/raised this invoice

// (Vendor)-[:FILED]->(GSTR1)
//   Vendor filed this GSTR-1 return for the period

// (Invoice)-[:REFLECTED_IN {auto_populated: true}]->(GSTR2B)
//   Invoice appears in buyer's GSTR-2B (system auto-populated)

// (Invoice)-[:CLAIMED_IN {itc_amount: 18000}]->(GSTR3B)
//   Buyer claimed ITC for this invoice in GSTR-3B

// (Invoice)-[:HAS_IRN]->(IRN)
//   Invoice has an e-invoice reference number

// (Taxpayer)-[:PAID_TAX]->(Payment)
//   Taxpayer made this GST payment

// (GSTR3B)-[:SETTLED_BY]->(Payment)
//   GSTR-3B tax liability settled by this payment

// (Vendor)-[:TRANSACTS_WITH]->(Vendor)
//   Circular trading detection: vendor sends money back through chain
//   properties: transaction_count, total_value, suspicious: true/false
