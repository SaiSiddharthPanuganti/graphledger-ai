import { useState, useMemo } from 'react';
import { MISMATCHES } from '../data/mockData';
import { exportITCCalculator } from '../utils/exportUtils';

// ── helpers ──────────────────────────────────────────────────────────────────
function inr(n) {
  return '₹' + Math.round(n).toLocaleString('en-IN');
}

// ── Section 1: ITC Eligibility Calculator ────────────────────────────────────
function EligibilityCalculator() {
  const [invoiceValue, setInvoiceValue] = useState('');
  const [gstRate, setGstRate] = useState('18');
  const [supplyType, setSupplyType] = useState('INTERSTATE');
  const [gstr2bStatus, setGstr2bStatus] = useState('PRESENT');
  const [irnValid, setIrnValid] = useState('YES');
  const [vendorFiling, setVendorFiling] = useState('REGULAR FILER');
  const [result, setResult] = useState(null);

  function calculate() {
    const val = parseFloat(invoiceValue) || 0;
    if (!val) return;
    const rate = parseFloat(gstRate) / 100;
    const taxable = val / (1 + rate);
    const totalGST = val - taxable;
    const halfGST = totalGST / 2;

    const blockingReasons = [];
    if (gstr2bStatus === 'ABSENT') blockingReasons.push('❌ Invoice not in GSTR-2B — Section 16(2)(aa) blocks ITC');
    if (irnValid === 'NO') blockingReasons.push('❌ Invalid IRN — GSTN may reject invoice');
    if (vendorFiling === 'NON-FILER') blockingReasons.push('❌ Vendor is non-filer — Section 16(2)(c) at risk');

    let eligibility = 'eligible';
    let eligibleITC = totalGST;
    if (blockingReasons.length >= 2 || gstr2bStatus === 'ABSENT') {
      eligibility = 'blocked';
      eligibleITC = 0;
    } else if (blockingReasons.length === 1) {
      eligibility = 'partial';
      eligibleITC = totalGST * 0.5;
    }

    // Rule 36(4): 105% cap
    const gstr2bAmount = gstr2bStatus === 'PRESENT' ? totalGST : 0;
    const cap105 = gstr2bAmount * 1.05;
    const claimStatus = eligibleITC <= cap105 ? '✅ Within cap' : '⚠️ Exceeds 105% cap';

    setResult({ taxable, gstRate, totalGST, halfGST, eligibility, eligibleITC, blockingReasons, gstr2bAmount, cap105, claimStatus, supplyType });
  }

  const statusLabel = result?.eligibility === 'eligible' ? '✅ FULLY ELIGIBLE'
    : result?.eligibility === 'partial' ? '⚠️ PARTIALLY ELIGIBLE'
    : '❌ BLOCKED';

  return (
    <div className="card" style={{ marginBottom: 24 }}>
      <div className="card-header">
        <h2 className="card-title">ITC Eligibility Calculator</h2>
        <p className="card-sub">Compute eligible ITC from invoice details</p>
      </div>
      <div className="calc-grid">
        {/* Left: Form */}
        <div className="calc-form">
          <div className="calc-field">
            <label>Invoice Value (₹)</label>
            <input className="calc-input" type="number" placeholder="e.g. 118000" value={invoiceValue} onChange={e => setInvoiceValue(e.target.value)} />
          </div>
          <div className="calc-field">
            <label>GST Rate</label>
            <select className="calc-select" value={gstRate} onChange={e => setGstRate(e.target.value)}>
              <option value="5">5%</option>
              <option value="12">12%</option>
              <option value="18">18%</option>
              <option value="28">28%</option>
            </select>
          </div>
          <div className="calc-field">
            <label>Supply Type</label>
            <div className="toggle-group">
              {['INTERSTATE', 'INTRASTATE'].map(v => (
                <button key={v} className={`toggle-btn${supplyType === v ? ' active' : ''}`} onClick={() => setSupplyType(v)}>{v}</button>
              ))}
            </div>
          </div>
          <div className="calc-field">
            <label>GSTR-2B Status</label>
            <div className="toggle-group">
              {['PRESENT', 'ABSENT'].map(v => (
                <button key={v} className={`toggle-btn${gstr2bStatus === v ? ' active' : ''}`} onClick={() => setGstr2bStatus(v)}>{v}</button>
              ))}
            </div>
          </div>
          <div className="calc-field">
            <label>IRN Valid</label>
            <div className="toggle-group">
              {['YES', 'NO'].map(v => (
                <button key={v} className={`toggle-btn${irnValid === v ? ' active' : ''}`} onClick={() => setIrnValid(v)}>{v}</button>
              ))}
            </div>
          </div>
          <div className="calc-field">
            <label>Vendor Filing Status</label>
            <select className="calc-select" value={vendorFiling} onChange={e => setVendorFiling(e.target.value)}>
              <option>REGULAR FILER</option>
              <option>OCCASIONAL FILER</option>
              <option>NON-FILER</option>
            </select>
          </div>
          <button className="btn-primary" style={{ marginTop: 4 }} onClick={calculate}>Calculate ITC</button>
        </div>

        {/* Right: Results */}
        <div>
          {result ? (
            <>
              <table className="breakdown-table" style={{ marginBottom: 14 }}>
                <tbody>
                  <tr><td>Taxable Value</td><td>{inr(result.taxable)}</td></tr>
                  <tr><td>GST Rate</td><td>{result.gstRate}%</td></tr>
                  {result.supplyType === 'INTRASTATE' ? (
                    <>
                      <tr><td>CGST ({result.gstRate / 2}%)</td><td>{inr(result.halfGST)}</td></tr>
                      <tr><td>SGST ({result.gstRate / 2}%)</td><td>{inr(result.halfGST)}</td></tr>
                    </>
                  ) : (
                    <tr><td>IGST ({result.gstRate}%)</td><td>{inr(result.totalGST)}</td></tr>
                  )}
                  <tr><td>Total GST</td><td>{inr(result.totalGST)}</td></tr>
                </tbody>
              </table>

              <div className={`eligibility-result ${result.eligibility}`}>
                <div className="eligibility-icon">{result.eligibility === 'eligible' ? '✅' : result.eligibility === 'partial' ? '⚠️' : '❌'}</div>
                <div className="eligibility-label">{statusLabel}</div>
                <div className="eligibility-amount">{inr(result.eligibleITC)}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>Eligible ITC Amount</div>
              </div>

              <div className="rule36-bar">
                <strong style={{ fontSize: 11 }}>Rule 36(4) Check</strong>
                <div style={{ marginTop: 4, color: 'var(--text-muted)', fontSize: 12 }}>
                  GSTR-2B shows {inr(result.gstr2bAmount)} → 105% cap = {inr(result.cap105)} → Your claim: {inr(result.eligibleITC)} → {result.claimStatus}
                </div>
              </div>

              {result.blockingReasons.length > 0 && (
                <div style={{ marginTop: 12 }}>
                  <div style={{ fontSize: 11, fontWeight: 700, marginBottom: 6, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '.5px' }}>Blocking Reasons</div>
                  {result.blockingReasons.map((r, i) => (
                    <div key={i} className="blocking-reason">{r}</div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)', fontSize: 13, flexDirection: 'column', gap: 8, padding: 40 }}>
              <span style={{ fontSize: 32 }}>🧮</span>
              <span>Fill in the form and click Calculate ITC to see results</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Section 2: ITC Reversal & Interest Calculator ────────────────────────────
function ReversalCalculator() {
  const sixMonthsAgo = new Date();
  sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);
  const todayStr = new Date().toISOString().split('T')[0];
  const sixMonthAgoStr = sixMonthsAgo.toISOString().split('T')[0];

  const [itcAmount, setItcAmount] = useState('');
  const [claimDate, setClaimDate] = useState(sixMonthAgoStr);
  const [reversalDate, setReversalDate] = useState(todayStr);
  const [reason, setReason] = useState('Invoice not in GSTR-2B (Sec 16(2)(aa))');
  const [includePenalty, setIncludePenalty] = useState(false);
  const [result, setResult] = useState(null);

  function calculate() {
    const itc = parseFloat(itcAmount) || 0;
    if (!itc) return;
    const d1 = new Date(claimDate);
    const d2 = new Date(reversalDate);
    const days = Math.max(0, Math.round((d2 - d1) / (1000 * 60 * 60 * 24)));
    const interest = itc * 0.18 * (days / 365);
    const penalty = includePenalty ? itc : 0;
    const total = itc + interest + penalty;
    setResult({ itc, days, interest, penalty, total, includePenalty });
  }

  return (
    <div className="card" style={{ marginBottom: 24 }}>
      <div className="card-header">
        <h2 className="card-title">ITC Reversal &amp; Interest Calculator</h2>
        <p className="card-sub">Calculate liability for wrongly availed ITC</p>
      </div>
      <div className="calc-grid">
        {/* Left: Form */}
        <div className="calc-form">
          <div className="calc-field">
            <label>ITC Amount Wrongly Claimed (₹)</label>
            <input className="calc-input" type="number" placeholder="e.g. 50000" value={itcAmount} onChange={e => setItcAmount(e.target.value)} />
          </div>
          <div className="calc-field">
            <label>Date of Wrong Claim</label>
            <input className="calc-input" type="date" value={claimDate} onChange={e => setClaimDate(e.target.value)} />
          </div>
          <div className="calc-field">
            <label>Date of Reversal / Today</label>
            <input className="calc-input" type="date" value={reversalDate} onChange={e => setReversalDate(e.target.value)} />
          </div>
          <div className="calc-field">
            <label>Reversal Reason</label>
            <select className="calc-select" value={reason} onChange={e => setReason(e.target.value)}>
              <option>Invoice not in GSTR-2B (Sec 16(2)(aa))</option>
              <option>Vendor Non-filer (Sec 16(2)(c))</option>
              <option>IRN Invalid / E-Way Bill Missing</option>
              <option>Ineligible under Sec 17(5) (blocked credits)</option>
              <option>Circular trading / Fraudulent invoice</option>
            </select>
          </div>
          <div className="calc-field">
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', textTransform: 'none', fontSize: 13, letterSpacing: 0, fontWeight: 500 }}>
              <input type="checkbox" checked={includePenalty} onChange={e => setIncludePenalty(e.target.checked)} style={{ width: 14, height: 14 }} />
              Include Penalty?
            </label>
          </div>
          <button className="btn-primary" style={{ marginTop: 4 }} onClick={calculate}>Calculate Reversal</button>
        </div>

        {/* Right: Results */}
        <div>
          {result ? (
            <>
              <table className="breakdown-table" style={{ marginBottom: 14 }}>
                <tbody>
                  <tr><td>ITC to Reverse</td><td>{inr(result.itc)}</td></tr>
                  <tr><td>Interest Period</td><td>{result.days} days</td></tr>
                  <tr><td>Interest Rate</td><td>18% p.a.</td></tr>
                  <tr><td>Interest Amount</td><td>{inr(result.interest)}</td></tr>
                  <tr><td>Penalty {result.includePenalty ? '(100%)' : ''}</td><td>{result.includePenalty ? inr(result.penalty) : 'N/A'}</td></tr>
                  <tr><td><strong>Total Liability</strong></td><td><strong>{inr(result.total)}</strong></td></tr>
                </tbody>
              </table>

              <div style={{ textAlign: 'center', marginBottom: 14 }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '.5px', marginBottom: 2 }}>Total Liability</div>
                <div className="liability-total">{inr(result.total)}</div>
              </div>

              <div className="legal-card">
                <p><strong>Interest:</strong> Section 50(3) CGST Act — 18% p.a. from date of availing to date of reversal</p>
                <p><strong>Penalty (if included):</strong> Section 122(1)(ii) — 100% of wrongfully availed ITC</p>
              </div>

              <div className="action-steps">
                <div style={{ fontSize: 11, fontWeight: 700, marginBottom: 8, color: 'var(--amber)', textTransform: 'uppercase', letterSpacing: '.5px' }}>⚡ Action Steps</div>
                <p>1. File DRC-03 form for voluntary reversal</p>
                <p>2. Pay interest along with reversal in GSTR-3B</p>
                <p>3. Maintain documentation for audit trail</p>
              </div>
            </>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)', fontSize: 13, flexDirection: 'column', gap: 8, padding: 40 }}>
              <span style={{ fontSize: 32 }}>💰</span>
              <span>Fill in the form and click Calculate Reversal to see liability</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Section 3: Batch Reversal from Reconciliation ────────────────────────────
function BatchReversal() {
  const [selected, setSelected] = useState(new Set());

  const atRisk = useMemo(() => {
    const both = MISMATCHES.filter(m => m.risk_level === 'CRITICAL' || m.risk_level === 'HIGH')
      .sort((a, b) => (b.itc_at_risk || 0) - (a.itc_at_risk || 0))
      .slice(0, 10);
    return both;
  }, []);

  const totalITC = useMemo(() => MISMATCHES.filter(m => m.risk_level === 'CRITICAL' || m.risk_level === 'HIGH').reduce((s, m) => s + (m.itc_at_risk || 0), 0), []);
  const totalInterest = totalITC * 0.18 * (6 / 12);
  const totalPenalty = totalITC;
  const totalExposure = totalITC + totalInterest + totalPenalty;

  function toggleRow(id) {
    setSelected(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  function toggleAll() {
    if (selected.size === atRisk.length) setSelected(new Set());
    else setSelected(new Set(atRisk.map(m => m.id)));
  }

  const selectedRows = atRisk.filter(m => selected.has(m.id));
  const selITC = selectedRows.reduce((s, m) => s + (m.itc_at_risk || 0), 0);
  const selInterest = selITC * 0.18 * (6 / 12);

  const riskColor = { CRITICAL: 'var(--critical)', HIGH: 'var(--high)', MEDIUM: 'var(--medium)' };

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="card-title">Batch ITC Reversal Estimate</h2>
        <p className="card-sub">Auto-calculated from current reconciliation data</p>
      </div>

      {/* Summary bar */}
      <div className="batch-stat-grid">
        {[
          { label: 'Total ITC to Reverse', value: inr(totalITC), color: 'var(--critical)' },
          { label: 'Interest Liability (18% × 6mo)', value: inr(totalInterest), color: 'var(--high)' },
          { label: 'Potential Penalty (100%)', value: inr(totalPenalty), color: '#7c3aed' },
          { label: 'Total Maximum Exposure', value: inr(totalExposure), color: 'var(--text-main)' },
        ].map((s, i) => (
          <div key={i} className="card" style={{ padding: '14px 16px', textAlign: 'center' }}>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6, fontWeight: 600 }}>{s.label}</div>
            <div style={{ fontSize: 18, fontWeight: 700, fontFamily: "'Space Mono',monospace", color: s.color }}>{s.value}</div>
          </div>
        ))}
      </div>

      {/* Table */}
      <div style={{ overflowX: 'auto', marginBottom: 14 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ background: 'var(--paper)' }}>
              <th style={{ padding: '8px 12px', textAlign: 'left' }}>
                <input type="checkbox" checked={selected.size === atRisk.length && atRisk.length > 0} onChange={toggleAll} />
              </th>
              {['Invoice', 'Supplier', 'Type', 'ITC at Risk', 'Interest (6mo)', 'Status'].map(h => (
                <th key={h} style={{ padding: '8px 12px', textAlign: 'left', fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '.5px' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {atRisk.map(m => {
              const interest6mo = (m.itc_at_risk || 0) * 0.18 * (6 / 12);
              return (
                <tr key={m.id} style={{ borderBottom: '1px solid var(--border)', background: selected.has(m.id) ? 'rgba(245,158,11,.04)' : undefined }}>
                  <td style={{ padding: '8px 12px' }}>
                    <input type="checkbox" checked={selected.has(m.id)} onChange={() => toggleRow(m.id)} />
                  </td>
                  <td style={{ padding: '8px 12px', fontFamily: "'Space Mono',monospace", fontSize: 12 }}>{m.invoice_no}</td>
                  <td style={{ padding: '8px 12px', fontSize: 12 }}>{m.supplier_gstin?.slice(0, 15) || '—'}</td>
                  <td style={{ padding: '8px 12px', fontSize: 12 }}>{m.mismatch_type?.replace(/_/g, ' ')}</td>
                  <td style={{ padding: '8px 12px', fontFamily: "'Space Mono',monospace", fontSize: 12, color: riskColor[m.risk_level] || 'inherit' }}>{inr(m.itc_at_risk || 0)}</td>
                  <td style={{ padding: '8px 12px', fontFamily: "'Space Mono',monospace", fontSize: 12, color: 'var(--high)' }}>{inr(interest6mo)}</td>
                  <td style={{ padding: '8px 12px' }}>
                    <span style={{ fontSize: 11, fontWeight: 600, padding: '2px 8px', borderRadius: 12, background: m.resolution_status === 'RESOLVED' ? 'rgba(34,197,94,.1)' : m.resolution_status === 'IN_PROGRESS' ? 'rgba(59,130,246,.1)' : 'rgba(239,68,68,.1)', color: m.resolution_status === 'RESOLVED' ? '#16a34a' : m.resolution_status === 'IN_PROGRESS' ? '#2563eb' : 'var(--critical)' }}>
                      {m.resolution_status || 'PENDING'}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Actions row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        {selected.size > 0 && (
          <div style={{ padding: '10px 16px', background: 'rgba(245,158,11,.08)', border: '1px solid rgba(245,158,11,.3)', borderRadius: 8, fontSize: 13 }}>
            <strong>{selected.size} selected</strong> — ITC: <span style={{ fontFamily: "'Space Mono',monospace", color: 'var(--critical)' }}>{inr(selITC)}</span> + Interest: <span style={{ fontFamily: "'Space Mono',monospace", color: 'var(--high)' }}>{inr(selInterest)}</span> = <span style={{ fontFamily: "'Space Mono',monospace", fontWeight: 700 }}>{inr(selITC + selInterest)}</span>
          </div>
        )}
        {selected.size > 0 && (
          <button className="btn-primary" onClick={() => alert(`Reversal initiated for ${selected.size} invoices.\nTotal: ${inr(selITC + selInterest)}`)}>
            Reverse Selected
          </button>
        )}
        <button className="btn-secondary" style={{ marginLeft: 'auto' }} onClick={exportITCCalculator}>
          📥 Export Reversal Schedule (CSV)
        </button>
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function ITCCalculator() {
  return (
    <div>
      <EligibilityCalculator />
      <ReversalCalculator />
      <BatchReversal />
    </div>
  );
}
