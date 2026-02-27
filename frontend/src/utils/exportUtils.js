/**
 * exportUtils.js — Page-aware CSV/TXT export helpers
 * =====================================================
 * Each function targets one page's data and downloads
 * a properly formatted CSV or text report.
 */

import {
  MISMATCHES,
  VENDORS,
  PREDICTIONS,
  ITC_CHAIN_HOPS,
  GRAPH_NODES,
  GRAPH_EDGES,
} from '../data/mockData';

// ── helpers ──────────────────────────────────────────────────────────────────
function downloadBlob(content, filename, mime = 'text/csv') {
  const bom = mime === 'text/csv' ? '\uFEFF' : ''; // BOM for Excel UTF-8
  const blob = new Blob([bom + content], { type: mime });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

function csvRow(cells) {
  return cells.map(c => {
    const s = String(c ?? '').replace(/"/g, '""');
    return /[,"\n]/.test(s) ? `"${s}"` : s;
  }).join(',');
}

function header(title) {
  return [
    `GraphLedger AI — ${title}`,
    `Generated: ${new Date().toLocaleString('en-IN')}`,
    '',
  ].join('\n');
}

// ── per-page exporters ────────────────────────────────────────────────────────

/** Overview — top-risk alert summary */
export function exportOverview() {
  const criticals = MISMATCHES.filter(m => m.risk_level === 'CRITICAL');
  const highs     = MISMATCHES.filter(m => m.risk_level === 'HIGH');
  const totalRisk = MISMATCHES.reduce((s, m) => s + (m.itc_at_risk || 0), 0);

  const rows = [
    csvRow(['Invoice No', 'Supplier GSTIN', 'Mismatch Type', 'Risk Level', 'ITC at Risk (₹)', 'Period', 'Root Cause', 'Status']),
    ...MISMATCHES.map(m => csvRow([
      m.invoice_no,
      m.supplier_gstin || m.gstin || '',
      m.mismatch_type,
      m.risk_level,
      m.itc_at_risk || '',
      m.period || '',
      m.root_cause || '',
      m.resolution_status || '',
    ])),
  ];

  const summary = [
    header('Executive Overview — ITC Risk Summary'),
    `Total Invoices Processed,${MISMATCHES.length}`,
    `Total ITC at Risk (₹),${totalRisk.toLocaleString('en-IN')}`,
    `CRITICAL Findings,${criticals.length}`,
    `HIGH Findings,${highs.length}`,
    `Match Rate,${((1 - MISMATCHES.length / 500) * 100).toFixed(1)}%`,
    '',
    ...rows,
  ].join('\n');

  downloadBlob(summary, 'graphledger-overview.csv');
}

/** Reconciliation — full mismatch table */
export function exportReconciliation() {
  const rows = [
    csvRow(['Invoice No', 'Supplier GSTIN', 'Mismatch Type', 'GSTR-1 Value (₹)', 'GSTR-2B Value (₹)', 'ITC at Risk (₹)', 'Period', 'Risk Level', 'Resolution Status', 'Root Cause']),
    ...MISMATCHES.map(m => csvRow([
      m.invoice_no,
      m.supplier_gstin || m.gstin || '',
      m.mismatch_type,
      m.gstr1_value || '',
      m.gstr2b_value || '',
      m.itc_at_risk || '',
      m.period || '',
      m.risk_level,
      m.resolution_status || 'PENDING',
      m.root_cause || '',
    ])),
  ];

  const totalRisk = MISMATCHES.reduce((s, m) => s + (m.itc_at_risk || 0), 0);
  const content = [
    header('ITC Reconciliation Report'),
    `Total Mismatches,${MISMATCHES.length}`,
    `Total ITC at Risk (₹),${totalRisk.toLocaleString('en-IN')}`,
    '',
    ...rows,
  ].join('\n');

  downloadBlob(content, 'graphledger-reconciliation.csv');
}

/** ITC Chain — hop-by-hop traversal */
export function exportITCChain() {
  const rows = [
    csvRow(['Hop #', 'Node Name', 'GSTIN', 'ITC Value (₹)', 'Status', 'Note']),
    ...ITC_CHAIN_HOPS.map((h, i) => csvRow([
      i + 1,
      h.name || '',
      h.gstin || '',
      h.itc_value || '',
      h.status || '',
      h.note || '',
    ])),
  ];

  const content = [
    header('ITC Chain Traversal Report'),
    `Chain Hops,${ITC_CHAIN_HOPS.length}`,
    '',
    ...rows,
  ].join('\n');

  downloadBlob(content, 'graphledger-itc-chain.csv');
}

/** Vendor Risk — compliance scores */
export function exportVendorRisk() {
  const rows = [
    csvRow(['Vendor Name', 'GSTIN', 'Sector', 'State', 'Compliance Score', 'Risk Category', 'Mismatch Count', 'ITC at Risk (₹)', 'Filing Streak (months)', 'Recommendation']),
    ...VENDORS.map(v => csvRow([
      v.name || '',
      v.gstin || '',
      v.sector || '',
      v.state || '',
      v.compliance_score ?? '',
      v.risk_category || v.category || '',
      v.mismatch_count ?? '',
      v.itc_at_risk ?? '',
      v.filing_streak ?? '',
      v.recommendation || '',
    ])),
  ];

  const content = [
    header('Vendor Risk Intelligence Report'),
    `Total Vendors,${VENDORS.length}`,
    `High/Critical Risk Vendors,${VENDORS.filter(v => ['CRITICAL','HIGH'].includes(v.risk_category || v.category)).length}`,
    '',
    ...rows,
  ].join('\n');

  downloadBlob(content, 'graphledger-vendor-risk.csv');
}

/** Audit Trail — full audit log */
export function exportAuditTrail() {
  const rows = [
    csvRow(['Audit ID', 'Invoice No', 'Mismatch Type', 'Risk Level', 'ITC at Risk (₹)', 'Root Cause', 'Legal Reference', 'Action Required', 'Status']),
    ...MISMATCHES.map((m, i) => csvRow([
      `AUD-${String(i + 1).padStart(4, '0')}`,
      m.invoice_no,
      m.mismatch_type,
      m.risk_level,
      m.itc_at_risk || '',
      m.root_cause || '',
      m.legal_ref || '',
      m.action || '',
      m.resolution_status || 'PENDING',
    ])),
  ];

  const content = [
    header('Explainable Audit Trail Report'),
    `Total Audit Entries,${MISMATCHES.length}`,
    `Critical,${MISMATCHES.filter(m => m.risk_level === 'CRITICAL').length}`,
    `High,${MISMATCHES.filter(m => m.risk_level === 'HIGH').length}`,
    '',
    ...rows,
  ].join('\n');

  downloadBlob(content, 'graphledger-audit-trail.csv');
}

/** Predictions — vendor risk forecast */
export function exportPredictions() {
  const data = PREDICTIONS || VENDORS;
  const rows = [
    csvRow(['Vendor Name', 'GSTIN', 'Current Risk Score', 'Predicted Risk Score', 'Trend', 'Risk Category', 'Key Factors']),
    ...data.map(p => csvRow([
      p.name || p.vendor || '',
      p.gstin || '',
      p.current_score ?? p.compliance_score ?? '',
      p.predicted_score ?? '',
      p.trend || '',
      p.risk_category || p.category || '',
      Array.isArray(p.factors) ? p.factors.join('; ') : (p.factors || ''),
    ])),
  ];

  const content = [
    header('Predictive Risk Model — Vendor Forecast'),
    `Vendors Analysed,${data.length}`,
    '',
    ...rows,
  ].join('\n');

  downloadBlob(content, 'graphledger-predictions.csv');
}

/** Graph Explorer — node + edge lists */
export function exportGraphExplorer() {
  const nodeRows = [
    '',
    '== NODES ==',
    csvRow(['Node ID', 'Type', 'Label', 'Properties']),
    ...(GRAPH_NODES || []).map(n => csvRow([
      n.id || '',
      n.type || n.group || '',
      n.label || n.name || '',
      JSON.stringify(n.properties || {}),
    ])),
  ];

  const edgeRows = [
    '',
    '== EDGES ==',
    csvRow(['Source', 'Target', 'Relationship', 'Weight']),
    ...(GRAPH_EDGES || []).map(e => csvRow([
      e.source || e.from || '',
      e.target || e.to || '',
      e.label || e.type || e.relationship || '',
      e.weight ?? '',
    ])),
  ];

  const content = [
    header('Knowledge Graph Export'),
    `Total Nodes,${(GRAPH_NODES || []).length}`,
    `Total Edges,${(GRAPH_EDGES || []).length}`,
    ...nodeRows,
    ...edgeRows,
  ].join('\n');

  downloadBlob(content, 'graphledger-knowledge-graph.csv');
}

/** OCR Upload — extraction history */
export function exportOCRHistory(uploads = []) {
  const rows = [
    csvRow(['Upload ID', 'Filename', 'Invoice No', 'Supplier GSTIN', 'Buyer GSTIN', 'Taxable Value (₹)', 'GST Amount (₹)', 'IRN', 'Confidence %', 'Validation Status', 'ITC at Risk (₹)', 'Uploaded At']),
    ...uploads.map(u => csvRow([
      u.upload_id || '',
      u.filename || '',
      u.fields?.invoice_no || '',
      u.fields?.supplier_gstin || '',
      u.fields?.buyer_gstin || '',
      u.fields?.taxable_value || '',
      (u.fields?.igst || 0) + (u.fields?.cgst || 0) + (u.fields?.sgst || 0),
      u.fields?.irn || '',
      u.overall_confidence ?? '',
      u.validation_status || '',
      u.itc_at_risk || '',
      u.extracted_at || '',
    ])),
  ];

  const content = [
    header('OCR Invoice Upload History'),
    `Total Uploads,${uploads.length}`,
    `Clean,${uploads.filter(u => u.validation_status === 'CLEAN').length}`,
    `Flagged,${uploads.filter(u => u.validation_status !== 'CLEAN').length}`,
    '',
    ...rows,
  ].join('\n');

  downloadBlob(content, 'graphledger-ocr-history.csv');
}

/** Traversal — not data-exportable, export as text summary */
export function exportTraversal() {
  const content = [
    header('Live Graph Traversal — Session Summary'),
    '',
    'Traversal modes available:',
    '  1. ITC Chain BFS   — Validates invoice → vendor → GSTR-1 → GSTR-2B links',
    '  2. Circular Fraud  — Detects ring transactions between vendors',
    '  3. GSTR Filing     — Simulates filing sequence and ITC eligibility',
    '',
    'Key GST Rules:',
    '  Section 16(2)(aa) CGST Act: ITC only allowed if invoice in GSTR-2B',
    '  Rule 36(4): ITC capped at 105% of GSTR-2B eligible amount',
    '  Section 50(3): 18% p.a. interest on wrongly availed ITC',
    '',
    'Export this page via the Knowledge Graph Export for node/edge data.',
  ].join('\n');

  downloadBlob(content, 'graphledger-traversal-summary.txt', 'text/plain');
}

// ── route → exporter map (used by Topbar) ────────────────────────────────────
export function exportITCCalculator() {
  const critical = MISMATCHES.filter(m => m.risk_level === 'CRITICAL');
  const high = MISMATCHES.filter(m => m.risk_level === 'HIGH');
  const both = [...critical, ...high].sort((a, b) => (b.itc_at_risk || 0) - (a.itc_at_risk || 0));
  const rows = [
    csvRow(['Invoice No', 'Mismatch Type', 'Risk Level', 'ITC at Risk (₹)', 'Interest 6mo (₹)', 'Total Liability (₹)', 'Status']),
    ...both.map(m => {
      const interest = (m.itc_at_risk || 0) * 0.18 * (6 / 12);
      return csvRow([m.invoice_no, m.mismatch_type, m.risk_level, m.itc_at_risk || 0, Math.round(interest), Math.round((m.itc_at_risk || 0) + interest), m.resolution_status || 'PENDING']);
    }),
  ];
  const totalITC = both.reduce((s, m) => s + (m.itc_at_risk || 0), 0);
  const totalInterest = totalITC * 0.18 * (6 / 12);
  const content = [
    header('ITC Reversal Schedule'),
    `Total ITC to Reverse (₹),${Math.round(totalITC).toLocaleString('en-IN')}`,
    `Total Interest Liability (₹),${Math.round(totalInterest).toLocaleString('en-IN')}`,
    `Total Exposure (₹),${Math.round(totalITC + totalInterest).toLocaleString('en-IN')}`,
    '',
    ...rows,
  ].join('\n');
  downloadBlob(content, 'graphledger-itc-reversal-schedule.csv');
}

export const PAGE_EXPORTERS = {
  '/':          exportOverview,
  '/recon':     exportReconciliation,
  '/chain':     exportITCChain,
  '/vendor':    exportVendorRisk,
  '/audit':     exportAuditTrail,
  '/predict':   exportPredictions,
  '/graph':     exportGraphExplorer,
  '/traversal': exportTraversal,
  '/ocr':       null,   // OCR passes uploads[] dynamically — handled in OCRUpload.jsx
  '/itc-calc':  exportITCCalculator,
};
