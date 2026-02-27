import { useState, useRef, useEffect } from 'react';
import { exportOCRHistory } from '../utils/exportUtils';

const MOCK_RESULT = {
  upload_id: "OCR-20241015143022",
  filename: "sample_invoice.pdf",
  source: "pdf",
  extracted_at: new Date().toISOString(),
  overall_confidence: 87.5,
  fields: {
    invoice_no: "INV-2024-1042",
    invoice_date: "15-Oct-2024",
    supplier_gstin: "27AABCM1234F1Z5",
    buyer_gstin: "29AADCV5678B1ZP",
    taxable_value: 665000,
    cgst: 0,
    sgst: 0,
    igst: 119700,
    total_value: 784700,
    irn: "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
    eway_bill_no: "321456789012",
    supply_type: "INTERSTATE",
    gst_rate: 18,
    irn_required: true,
    ewb_required: true,
  },
  confidence: {
    invoice_no: 0.9, invoice_date: 0.9, supplier_gstin: 1.0,
    buyer_gstin: 1.0, taxable_value: 0.95, total_tax: 0.95,
    irn: 1.0, eway_bill: 1.0
  },
  mismatches_detected: [],
  mismatch_count: 0,
  itc_at_risk: 0,
  validation_status: "CLEAN"
};

function fmtBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1048576).toFixed(1) + ' MB';
}

function fmtCurrency(val) {
  if (val === 0) return '₹0';
  return '₹' + Number(val).toLocaleString('en-IN');
}

function ConfDots({ score }) {
  const filled = score != null ? Math.round(score / 0.2) : 0;
  return (
    <span className="conf-dots">
      {[0,1,2,3,4].map(i => (
        <span key={i} className={`conf-dot${i < filled ? ' filled' : ''}`} />
      ))}
    </span>
  );
}

function ValidationBadge({ status }) {
  const cls = status === 'CLEAN' ? 'vs-clean' : status === 'CRITICAL' ? 'vs-critical' : 'vs-flagged';
  return <span className={`validation-status-badge ${cls}`}>{status}</span>;
}

export default function OCRUpload() {
  const [file, setFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [toast, setToast] = useState(null);
  const fileInputRef = useRef(null);

  // Listen for export event dispatched by Topbar
  useEffect(() => {
    const handler = () => exportOCRHistory(history);
    document.addEventListener('ocr-export', handler);
    return () => document.removeEventListener('ocr-export', handler);
  }, [history]);

  function showToast(msg) {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
  }

  function handleFile(f) {
    if (!f) return;
    setFile(f);
    setResult(null);
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }

  function handleChange(e) {
    const f = e.target.files[0];
    if (f) handleFile(f);
  }

  async function handleExtract() {
    if (!file) return;
    setLoading(true);
    try {
      const form = new FormData();
      form.append('file', file);
      const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001';
      const res = await fetch(`${API_BASE}/api/ocr/upload`, {
        method: 'POST',
        body: form,
      });
      if (!res.ok) throw new Error('API error');
      const data = await res.json();
      setResult(data);
      setHistory(prev => [data, ...prev]);
    } catch {
      // API offline — use mock
      const mock = { ...MOCK_RESULT, filename: file.name, extracted_at: new Date().toISOString() };
      setResult(mock);
      setHistory(prev => [mock, ...prev]);
    } finally {
      setLoading(false);
    }
  }

  function handleDownloadAudit() {
    if (!result) return;
    const f = result.fields;
    const lines = [
      `GraphLedger AI — OCR Audit Report`,
      `Upload ID: ${result.upload_id}`,
      `File: ${result.filename}`,
      `Extracted At: ${result.extracted_at}`,
      `Overall Confidence: ${result.overall_confidence}%`,
      `Validation Status: ${result.validation_status}`,
      ``,
      `── Extracted Fields ──`,
      `Invoice No: ${f.invoice_no}`,
      `Invoice Date: ${f.invoice_date}`,
      `Supplier GSTIN: ${f.supplier_gstin}`,
      `Buyer GSTIN: ${f.buyer_gstin}`,
      `Taxable Value: ${fmtCurrency(f.taxable_value)}`,
      `CGST: ${fmtCurrency(f.cgst)}`,
      `SGST: ${fmtCurrency(f.sgst)}`,
      `IGST: ${fmtCurrency(f.igst)}`,
      `Total Value: ${fmtCurrency(f.total_value)}`,
      `IRN: ${f.irn}`,
      `E-Way Bill No: ${f.eway_bill_no}`,
      `Supply Type: ${f.supply_type}`,
      `GST Rate: ${f.gst_rate}%`,
      ``,
      `── Mismatches ──`,
      result.mismatch_count === 0
        ? 'None — All validations passed.'
        : result.mismatches_detected.map(m => `[${m.risk}] ${m.type}: ${m.description} | ITC at Risk: ${fmtCurrency(m.itc_at_risk)}`).join('\n'),
    ];
    const blob = new Blob([lines.join('\n')], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit_${result.upload_id}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }

  // Stats derived from history
  const totalUploaded = history.length;
  const totalClean = history.filter(h => h.validation_status === 'CLEAN').length;
  const totalFlagged = history.filter(h => h.validation_status !== 'CLEAN').length;
  const totalITCRisk = history.reduce((acc, h) => acc + (h.itc_at_risk || 0), 0);

  // Extracted fields table rows
  const fieldRows = result ? [
    { label: 'Invoice No', value: result.fields.invoice_no, conf: result.confidence.invoice_no },
    { label: 'Invoice Date', value: result.fields.invoice_date, conf: result.confidence.invoice_date },
    { label: 'Supplier GSTIN', value: result.fields.supplier_gstin, conf: result.confidence.supplier_gstin },
    { label: 'Buyer GSTIN', value: result.fields.buyer_gstin, conf: result.confidence.buyer_gstin },
    { label: 'Taxable Value', value: fmtCurrency(result.fields.taxable_value), conf: result.confidence.taxable_value },
    { label: 'CGST', value: fmtCurrency(result.fields.cgst), conf: result.confidence.total_tax },
    { label: 'SGST', value: fmtCurrency(result.fields.sgst), conf: result.confidence.total_tax },
    { label: 'IGST', value: fmtCurrency(result.fields.igst), conf: result.confidence.total_tax },
    { label: 'IRN', value: (result.fields.irn || '').slice(0, 20) + '…', conf: result.confidence.irn },
    { label: 'E-Way Bill No', value: result.fields.eway_bill_no, conf: result.confidence.eway_bill },
    { label: 'Supply Type', value: result.fields.supply_type, conf: null },
    { label: 'GST Rate', value: result.fields.gst_rate + '%', conf: null },
  ] : [];

  return (
    <div>
      {/* ── Section 1: Stats + Upload Zone ── */}
      <div className="ocr-stats">
        <div className="ocr-stat-card card">
          <div className="ocr-stat-label">Total Uploaded</div>
          <div className="ocr-stat-val">{totalUploaded}</div>
        </div>
        <div className="ocr-stat-card card">
          <div className="ocr-stat-label">Clean</div>
          <div className="ocr-stat-val" style={{ color: 'var(--low)' }}>{totalClean}</div>
        </div>
        <div className="ocr-stat-card card">
          <div className="ocr-stat-label">Flagged</div>
          <div className="ocr-stat-val" style={{ color: 'var(--critical)' }}>{totalFlagged}</div>
        </div>
        <div className="ocr-stat-card card">
          <div className="ocr-stat-label">Total ITC at Risk</div>
          <div className="ocr-stat-val" style={{ color: 'var(--critical)' }}>{fmtCurrency(totalITCRisk)}</div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-title">Invoice OCR Upload</div>

        {/* Drop Zone */}
        <div
          className={`drop-zone${dragOver ? ' drag-over' : ''}`}
          onDragOver={e => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <div className="drop-zone-icon">📄</div>
          <div className="drop-zone-title">Drop PDF or Image Invoice Here</div>
          <div className="drop-zone-sub">Supports: PDF, PNG, JPG — Max 10MB</div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.png,.jpg,.jpeg"
            style={{ display: 'none' }}
            onChange={handleChange}
          />
        </div>

        {/* File chip */}
        {file && (
          <div style={{ marginBottom: 16 }}>
            <span className="file-chip">
              📎 {file.name} &nbsp;·&nbsp; {fmtBytes(file.size)}
              <span
                className="file-chip-remove"
                onClick={e => { e.stopPropagation(); setFile(null); setResult(null); }}
              >✕</span>
            </span>
          </div>
        )}

        <button
          className="btn btn-amber"
          onClick={handleExtract}
          disabled={!file || loading}
          style={{ minWidth: 180 }}
        >
          {loading ? (
            <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className="loading-spin" /> Analysing invoice...
            </span>
          ) : 'Extract & Validate'}
        </button>
      </div>

      {/* ── Section 2: Extraction Results ── */}
      {result && (
        <div className="ocr-results">
          {/* Left: Extracted Fields */}
          <div className="card">
            <div className="card-title">Extracted Fields</div>
            <table className="field-table">
              <thead>
                <tr>
                  <td style={{ fontWeight: 700, color: 'var(--text-muted)', fontSize: 10, textTransform: 'uppercase' }}>Field</td>
                  <td style={{ fontWeight: 700, color: 'var(--text-muted)', fontSize: 10, textTransform: 'uppercase' }}>Value</td>
                  <td style={{ fontWeight: 700, color: 'var(--text-muted)', fontSize: 10, textTransform: 'uppercase' }}>Confidence</td>
                </tr>
              </thead>
              <tbody>
                {fieldRows.map(row => (
                  <tr key={row.label}>
                    <td>{row.label}</td>
                    <td style={{ fontFamily: "'Space Mono', monospace", fontSize: 11, color: 'var(--text-main)' }}>{row.value}</td>
                    <td>
                      {row.conf != null
                        ? <ConfDots score={row.conf} />
                        : <span style={{ color: 'var(--text-muted)', fontSize: 10 }}>—</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="conf-bar-wrap">
              <div className="conf-bar-label">Overall Confidence: {result.overall_confidence}%</div>
              <div className="conf-bar">
                <div className="conf-bar-fill" style={{ width: result.overall_confidence + '%' }} />
              </div>
            </div>
          </div>

          {/* Right: Validation Result */}
          <div className="card">
            <div className="card-title">Validation Result</div>
            <ValidationBadge status={result.validation_status} />

            {result.mismatch_count === 0 ? (
              <div style={{ marginTop: 16, display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ fontSize: 28 }}>✅</span>
                <span style={{ fontSize: 13, color: '#166534' }}>All validations passed. ITC may be claimed.</span>
              </div>
            ) : (
              result.mismatches_detected.map((m, i) => {
                const cls = m.risk?.toLowerCase() === 'critical' ? 'critical' : m.risk?.toLowerCase() === 'high' ? 'high' : 'medium';
                return (
                  <div key={i} className={`mismatch-alert ${cls}`}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <span className="badge" style={{ background: cls === 'critical' ? '#fee2e2' : cls === 'high' ? '#ffedd5' : '#fef9c3', color: cls === 'critical' ? '#b91c1c' : cls === 'high' ? '#c2410c' : '#a16207' }}>{m.risk}</span>
                      <span className="mismatch-type">{m.type}</span>
                    </div>
                    <div className="mismatch-desc">{m.description}</div>
                    {m.itc_at_risk != null && <div className="mismatch-itc">ITC at Risk: {fmtCurrency(m.itc_at_risk)}</div>}
                    {m.legal_ref && <div className="mismatch-legal">📜 {m.legal_ref}</div>}
                    {m.action && <div className="mismatch-action">⚡ {m.action}</div>}
                  </div>
                );
              })
            )}

            <div style={{ marginTop: 20, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              {result.mismatch_count > 0 && (
                <button
                  className="btn btn-amber"
                  onClick={() => showToast('Invoice added to reconciliation queue')}
                >
                  Add to Reconciliation
                </button>
              )}
              <button className="btn btn-outline" onClick={handleDownloadAudit}>
                ⬇ Download Audit Report
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Section 3: Upload History ── */}
      <div className="card">
        <div className="card-title">Upload History</div>
        {history.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '32px 0', color: 'var(--text-muted)', fontSize: 13 }}>
            No invoices uploaded yet
          </div>
        ) : (
          <div className="table-wrap">
            <table className="ocr-history-table">
              <thead>
                <tr>
                  <th>Upload ID</th>
                  <th>File</th>
                  <th>Date</th>
                  <th>Fields Extracted</th>
                  <th>Confidence</th>
                  <th>Status</th>
                  <th>ITC at Risk</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {history.map((h, i) => {
                  const statCls = h.validation_status === 'CLEAN'
                    ? 'badge-low'
                    : h.validation_status === 'CRITICAL'
                    ? 'badge-critical'
                    : 'badge-high';
                  return (
                    <tr key={i}>
                      <td className="mono">{h.upload_id}</td>
                      <td>{h.filename}</td>
                      <td style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                        {new Date(h.extracted_at).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })}
                      </td>
                      <td className="mono">{Object.keys(h.fields || {}).length}</td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <div className="conf-bar" style={{ width: 60 }}>
                            <div className="conf-bar-fill" style={{ width: h.overall_confidence + '%' }} />
                          </div>
                          <span className="mono" style={{ fontSize: 10 }}>{h.overall_confidence}%</span>
                        </div>
                      </td>
                      <td><span className={`badge ${statCls}`}>{h.validation_status}</span></td>
                      <td className="mono" style={{ color: h.itc_at_risk > 0 ? 'var(--critical)' : 'var(--low)' }}>
                        {fmtCurrency(h.itc_at_risk)}
                      </td>
                      <td>
                        <button
                          className="btn btn-outline"
                          style={{ fontSize: 11, padding: '4px 10px' }}
                          onClick={() => setResult(h)}
                        >
                          View Details
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Toast */}
      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}
