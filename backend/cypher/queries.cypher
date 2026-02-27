// ============================================================
// GraphLedger AI — Core Cypher Traversal Queries
// Multi-hop reconciliation & fraud detection
// ============================================================

// ─── QUERY 1: Full Multi-Hop ITC Validation ──────────────────
// Traverses: Taxpayer → Invoice → Vendor → GSTR1 → GSTR2B → IRN
// Validates each hop and returns risk assessment
MATCH (t:Taxpayer)-[:PURCHASED]->(inv:Invoice)-[:ISSUED_BY]->(v:Vendor)
OPTIONAL MATCH (inv)-[:HAS_IRN]->(irn:IRN)
OPTIONAL MATCH (inv)-[:REFLECTED_IN]->(g2b:GSTR2B)
OPTIONAL MATCH (inv)-[:CLAIMED_IN]->(g3b:GSTR3B)
OPTIONAL MATCH (v)-[:FILED]->(g1:GSTR1 {period: inv.period})
OPTIONAL MATCH (t)-[:PAID_TAX]->(pmt:Payment)
RETURN
  inv.invoice_id                          AS invoice_id,
  inv.invoice_number                      AS invoice_number,
  inv.total_gst                           AS gst_amount,
  inv.period                              AS period,
  v.gstin                                 AS vendor_gstin,
  v.name                                  AS vendor_name,
  v.compliance_score                      AS vendor_score,
  CASE WHEN irn IS NOT NULL AND irn.valid = true THEN true ELSE false END AS irn_valid,
  CASE WHEN g2b IS NOT NULL THEN true ELSE false END                      AS in_gstr2b,
  CASE WHEN g1 IS NOT NULL AND g1.filed = true THEN true ELSE false END   AS vendor_filed,
  CASE WHEN g3b IS NOT NULL AND g3b.filed = true THEN true ELSE false END AS itc_claimed,
  inv.risk_score                          AS risk_score,
  inv.risk_category                       AS risk_category,
  inv.status                              AS status
ORDER BY inv.risk_score DESC;

// ─── QUERY 2: Vendor Risk Profile ────────────────────────────
// Aggregates invoice-level risk into vendor compliance score
MATCH (v:Vendor)<-[:ISSUED_BY]-(inv:Invoice)
WITH v,
  count(inv)                              AS total_invoices,
  sum(inv.total_gst)                      AS total_gst_value,
  sum(CASE WHEN inv.irn_valid = true THEN 1 ELSE 0 END)   AS valid_irn_count,
  sum(CASE WHEN inv.in_gstr2b = true THEN 1 ELSE 0 END)   AS in_2b_count,
  sum(CASE WHEN inv.vendor_filed = true THEN 1 ELSE 0 END) AS filed_count,
  sum(CASE WHEN inv.risk_category IN ['HIGH','CRITICAL'] THEN inv.total_gst ELSE 0 END) AS high_risk_gst
RETURN
  v.gstin             AS gstin,
  v.name              AS name,
  v.compliance_score  AS compliance_score,
  v.risk_category     AS risk_category,
  total_invoices,
  total_gst_value,
  round(toFloat(valid_irn_count) / total_invoices * 100, 2)  AS irn_validity_pct,
  round(toFloat(in_2b_count) / total_invoices * 100, 2)      AS gstr2b_reflection_pct,
  round(toFloat(filed_count) / total_invoices * 100, 2)      AS filing_compliance_pct,
  high_risk_gst       AS at_risk_gst_exposure
ORDER BY v.compliance_score ASC;

// ─── QUERY 3: Circular Trading Detection ─────────────────────
// Detects cycles of length 3-5 in vendor transaction graph
// Circular trading = fake invoices cycling money back to origin
// (Used to fraudulently inflate ITC claims)
MATCH cycle = (v1:Vendor)-[:TRANSACTS_WITH*3..5]->(v1)
WHERE ALL(r IN relationships(cycle) WHERE r.suspicious = true)
RETURN
  [node IN nodes(cycle) | node.gstin]    AS cycle_gstins,
  [node IN nodes(cycle) | node.name]     AS cycle_names,
  length(cycle)                          AS cycle_length,
  reduce(total = 0, r IN relationships(cycle) | total + r.total_value) AS total_circular_value
ORDER BY total_circular_value DESC
LIMIT 20;

// ─── QUERY 4: Suspicious Vendor Cluster (High Degree) ────────
// Vendors with unusually high connections = potential shell network
// Degree centrality > threshold indicates suspicious hub behavior
MATCH (v:Vendor)-[:TRANSACTS_WITH]-(connected:Vendor)
WITH v, count(DISTINCT connected) AS connection_count
WHERE connection_count >= 5
OPTIONAL MATCH (v)<-[:ISSUED_BY]-(inv:Invoice)
WITH v, connection_count, count(inv) AS invoice_count,
  avg(inv.risk_score) AS avg_risk
RETURN
  v.gstin             AS gstin,
  v.name              AS name,
  v.compliance_score  AS compliance_score,
  connection_count    AS vendor_connections,
  invoice_count,
  round(avg_risk, 2)  AS avg_invoice_risk,
  'SUSPICIOUS_HUB'    AS flag
ORDER BY connection_count DESC;

// ─── QUERY 5: Missing ITC Risk (Reconciliation Gap) ──────────
// Find invoices claimed in GSTR-3B but NOT in GSTR-2B
// This is the #1 source of GST notices from tax authorities
MATCH (t:Taxpayer)-[:PURCHASED]->(inv:Invoice)-[:CLAIMED_IN]->(g3b:GSTR3B)
WHERE NOT (inv)-[:REFLECTED_IN]->(:GSTR2B)
RETURN
  inv.invoice_id      AS invoice_id,
  inv.total_gst       AS gst_claimed,
  inv.period          AS period,
  g3b.gstr3b_id       AS gstr3b_id,
  'ITC_CLAIMED_NOT_IN_2B' AS risk_type,
  'HIGH'              AS risk_level;

// ─── QUERY 6: Vendor Filing Gap Analysis ─────────────────────
// Detect vendors who skipped GSTR-1 filing for any period
// Non-filing vendors = buyer cannot claim ITC safely
MATCH (v:Vendor)<-[:ISSUED_BY]-(inv:Invoice)
WHERE NOT (v)-[:FILED]->(:GSTR1 {period: inv.period})
WITH v, collect(DISTINCT inv.period) AS missing_periods,
  count(inv) AS affected_invoices,
  sum(inv.total_gst) AS at_risk_itc
RETURN
  v.gstin             AS vendor_gstin,
  v.name              AS vendor_name,
  missing_periods,
  affected_invoices,
  at_risk_itc,
  'NON_FILER_RISK'    AS risk_type;

// ─── QUERY 7: Dashboard Summary KPIs ─────────────────────────
MATCH (t:Taxpayer)-[:PURCHASED]->(inv:Invoice)
RETURN
  count(inv)                              AS total_invoices,
  sum(inv.total_gst)                      AS total_itc_pool,
  sum(CASE WHEN inv.status = 'MATCHED'   THEN inv.total_gst ELSE 0 END) AS clean_itc,
  sum(CASE WHEN inv.risk_category = 'HIGH'     THEN inv.total_gst ELSE 0 END) AS high_risk_itc,
  sum(CASE WHEN inv.risk_category = 'CRITICAL' THEN inv.total_gst ELSE 0 END) AS critical_itc,
  sum(CASE WHEN inv.risk_category = 'MEDIUM'   THEN inv.total_gst ELSE 0 END) AS medium_risk_itc,
  round(toFloat(sum(CASE WHEN inv.status = 'MISMATCHED' THEN 1 ELSE 0 END)) / count(inv) * 100, 2) AS mismatch_pct;
