import { useState } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement, PointElement, Filler, Tooltip, Legend } from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import { MISMATCHES, PAYMENT_OVERDUE } from '../data/mockData';
import { inr, mismatchIcon } from '../utils/formatters';
import RiskBadge from '../components/ui/RiskBadge';
import StatusBadge from '../components/ui/StatusBadge';
import Modal from '../components/ui/Modal';
import { generateAuditText } from '../utils/auditGenerator';

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, Filler, Tooltip, Legend);

// Payment status badge helper
function PaymentBadge({ status, daysLeft }) {
  const styles = {
    PAID:               { bg: '#dcfce7', color: '#16a34a', label: '✅ Paid' },
    PAID_AFTER_180_DAYS:{ bg: '#fef3c7', color: '#d97706', label: '⚠ Late Pay' },
    UNPAID_OVERDUE:     { bg: '#fee2e2', color: '#dc2626', label: '🔴 OVERDUE' },
    PAYMENT_PENDING:    { bg: '#dbeafe', color: '#2563eb', label: `⏳ ${daysLeft}d left` },
  };
  const s = styles[status] || styles.PAID;
  return (
    <span style={{ background: s.bg, color: s.color, borderRadius: 4, padding: '2px 7px', fontSize: 10, fontWeight: 700 }}>
      {s.label}
    </span>
  );
}

export default function Reconciliation() {
  const [search, setSearch] = useState('');
  const [riskFilter, setRiskFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [modalId, setModalId] = useState(null);
  const [showPaymentPanel, setShowPaymentPanel] = useState(false);

  const filtered = MISMATCHES.filter(m => {
    const matchSearch = !search || m.invoice_no.toLowerCase().includes(search) || m.supplier_gstin.toLowerCase().includes(search);
    const matchRisk = !riskFilter || m.risk_level === riskFilter;
    const matchType = !typeFilter || m.mismatch_type === typeFilter;
    return matchSearch && matchRisk && matchType;
  });

  const modalMismatch = MISMATCHES.find(x => x.id === modalId);

  const overdueCount   = PAYMENT_OVERDUE.filter(p => p.payment_status === 'UNPAID_OVERDUE').length;
  const overdueITC     = PAYMENT_OVERDUE.filter(p => p.payment_status === 'UNPAID_OVERDUE').reduce((s, p) => s + p.itc_value, 0);
  const interestTotal  = PAYMENT_OVERDUE.filter(p => p.payment_status === 'UNPAID_OVERDUE').reduce((s, p) => s + p.interest_liability, 0);
  const warningCount   = PAYMENT_OVERDUE.filter(p => p.payment_status === 'PAYMENT_PENDING').length;

  const itcTrendData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'],
    datasets: [{
      label: 'ITC at Risk (₹)',
      data: [82000, 95000, 71000, 118000, 143000, 99000, 87000, 165000],
      borderColor: '#f59e0b',
      backgroundColor: 'rgba(245,158,11,.1)',
      fill: true,
      tension: .4,
      pointBackgroundColor: '#f59e0b',
    }],
  };

  const resolutionData = {
    labels: ['PENDING', 'IN_PROGRESS', 'RESOLVED'],
    datasets: [{
      label: 'Count',
      data: [6, 3, 1],
      backgroundColor: ['#fde68a', '#bfdbfe', '#bbf7d0'],
      borderRadius: 6,
    }],
  };

  return (
    <div>
      {/* ── Section 16(2)(b) Alert Banner ── */}
      {overdueCount > 0 && (
        <div style={{ background: '#fef2f2', border: '1.5px solid #fca5a5', borderRadius: 10, padding: '14px 18px', marginBottom: 20, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ fontSize: 22 }}>🔴</span>
            <div>
              <div style={{ fontWeight: 700, fontSize: 13, color: '#dc2626' }}>
                Section 16(2)(b) Alert — {overdueCount} Invoice{overdueCount > 1 ? 's' : ''} Overdue 180 Days
              </div>
              <div style={{ fontSize: 11, color: '#6b7280', marginTop: 3 }}>
                ITC Reversal Required: <strong style={{ color: '#dc2626' }}>{inr(overdueITC)}</strong>
                &nbsp;·&nbsp;Interest Liability: <strong style={{ color: '#dc2626' }}>{inr(interestTotal)}</strong>
                &nbsp;·&nbsp;{warningCount} invoice{warningCount !== 1 ? 's' : ''} approaching deadline
              </div>
            </div>
          </div>
          <button
            className="btn btn-outline"
            style={{ fontSize: 11, padding: '6px 14px', borderColor: '#dc2626', color: '#dc2626', whiteSpace: 'nowrap' }}
            onClick={() => setShowPaymentPanel(p => !p)}
          >
            {showPaymentPanel ? 'Hide' : 'View Details'}
          </button>
        </div>
      )}

      {/* ── 180-Day Payment Compliance Panel ── */}
      {showPaymentPanel && (
        <div className="card" style={{ marginBottom: 24, borderLeft: '4px solid #dc2626' }}>
          <div className="card-title">⏱ Section 16(2)(b) — 180-Day Payment Compliance Tracker</div>
          <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 14 }}>
            Under Section 16(2)(b) CGST Act, ITC must be reversed if supplier is not paid within 180 days of invoice date.
            Interest at <strong>18% p.a.</strong> applies from original claim date (Section 50(3)).
            ITC is <strong>re-claimable</strong> once payment is made.
          </div>
          <div className="kpi-grid" style={{ marginBottom: 16 }}>
            <div className="kpi-card" style={{ padding: '12px 16px' }}>
              <div className="kpi-label">Overdue &gt;180 Days</div>
              <div className="kpi-val kpi-critical">{overdueCount}</div>
              <div className="kpi-sub">ITC reversal required now</div>
            </div>
            <div className="kpi-card" style={{ padding: '12px 16px' }}>
              <div className="kpi-label">ITC to Reverse</div>
              <div className="kpi-val kpi-critical">{inr(overdueITC)}</div>
              <div className="kpi-sub">GSTR-3B Table 4(B)(2)</div>
            </div>
            <div className="kpi-card" style={{ padding: '12px 16px' }}>
              <div className="kpi-label">Interest Liability</div>
              <div className="kpi-val" style={{ color: 'var(--high)' }}>{inr(interestTotal)}</div>
              <div className="kpi-sub">@ 18% p.a. · Sec 50(3)</div>
            </div>
            <div className="kpi-card" style={{ padding: '12px 16px' }}>
              <div className="kpi-label">Approaching Deadline</div>
              <div className="kpi-val" style={{ color: 'var(--medium)' }}>{warningCount}</div>
              <div className="kpi-sub">Pay within 30 days to retain ITC</div>
            </div>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Invoice No</th>
                  <th>Supplier</th>
                  <th>Invoice Date</th>
                  <th>Days Old</th>
                  <th>ITC Value</th>
                  <th>Interest @18%</th>
                  <th>Total Exposure</th>
                  <th>Status</th>
                  <th>Action Required</th>
                </tr>
              </thead>
              <tbody>
                {PAYMENT_OVERDUE.map(p => (
                  <tr key={p.invoice_id}>
                    <td className="mono">{p.invoice_no}</td>
                    <td style={{ fontSize: 10 }}>{p.supplier_name}</td>
                    <td className="mono">{p.invoice_date}</td>
                    <td className="mono" style={{ color: p.days_old > 180 ? 'var(--critical)' : 'var(--medium)', fontWeight: 700 }}>{p.days_old}d</td>
                    <td className="mono">{inr(p.itc_value)}</td>
                    <td className="mono" style={{ color: 'var(--high)' }}>{inr(p.interest_liability)}</td>
                    <td className="mono" style={{ color: 'var(--critical)', fontWeight: 700 }}>{inr(p.itc_value + p.interest_liability)}</td>
                    <td><PaymentBadge status={p.payment_status} daysLeft={p.days_left} /></td>
                    <td style={{ fontSize: 10, color: '#6b7280' }}>{p.action}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Mismatch Table ── */}
      <div className="filter-bar">
        <input
          className="search-input"
          placeholder="🔍 Search by invoice, GSTIN..."
          value={search}
          onChange={e => setSearch(e.target.value.toLowerCase())}
        />
        <select className="filter-sel" value={riskFilter} onChange={e => setRiskFilter(e.target.value)}>
          <option value="">All Risk Levels</option>
          <option value="CRITICAL">🔴 Critical</option>
          <option value="HIGH">🟠 High</option>
          <option value="MEDIUM">🟡 Medium</option>
          <option value="LOW">🟢 Low</option>
        </select>
        <select className="filter-sel" value={typeFilter} onChange={e => setTypeFilter(e.target.value)}>
          <option value="">All Types</option>
          <option value="IRN_MISMATCH">IRN Mismatch</option>
          <option value="INVOICE_MISSING_2B">Missing in 2B</option>
          <option value="AMOUNT_MISMATCH">Amount Mismatch</option>
          <option value="GSTIN_MISMATCH">GSTIN Mismatch</option>
          <option value="DATE_MISMATCH">Date Mismatch</option>
          <option value="EWAYBILL_MISSING">E-Way Bill</option>
          <option value="PAYMENT_OVERDUE_180_DAYS">⏱ 180-Day Overdue</option>
        </select>
      </div>

      <div className="table-wrap" style={{ marginBottom: '24px' }}>
        <table>
          <thead>
            <tr>
              <th>Invoice No</th><th>Supplier GSTIN</th><th>Mismatch Type</th>
              <th>GSTR-1 ₹</th><th>GSTR-2B ₹</th><th>ITC at Risk</th>
              <th>Period</th><th>Risk</th><th>Status</th><th>Action</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(m => (
              <tr key={m.id} style={m.mismatch_type === 'PAYMENT_OVERDUE_180_DAYS' ? { background: '#fff7f7' } : {}}>
                <td className="mono">{m.invoice_no}</td>
                <td className="mono" style={{ fontSize: '10px' }}>{m.supplier_gstin}</td>
                <td style={{ fontSize: '11px' }}>{mismatchIcon(m.mismatch_type)} {m.mismatch_type}</td>
                <td className="mono">{inr(m.gstr1_value)}</td>
                <td className="mono">{inr(m.gstr2b_value)}</td>
                <td className="mono" style={{ color: 'var(--critical)', fontWeight: 700 }}>{inr(m.itc_at_risk)}</td>
                <td className="mono">{m.period}</td>
                <td><RiskBadge risk={m.risk_level} /></td>
                <td><StatusBadge status={m.status} /></td>
                <td>
                  <button className="btn btn-outline" style={{ fontSize: '10px', padding: '4px 8px' }}
                    onClick={() => { setModalId(m.id); setModalOpen(true); }}>Audit</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="two-col">
        <div className="card">
          <div className="card-title">ITC at Risk Trend (Jan–Aug 2024)</div>
          <Line data={itcTrendData} options={{
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
              y: { ticks: { callback: v => '₹' + Math.round(v / 1000) + 'K', font: { family: 'Space Mono', size: 9 } }, grid: { color: '#f1f5f9' } },
              x: { ticks: { font: { family: 'Space Mono', size: 9 } }, grid: { display: false } }
            }
          }} />
        </div>
        <div className="card">
          <div className="card-title">Resolution Status</div>
          <Bar data={resolutionData} options={{
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
              y: { ticks: { stepSize: 1, font: { family: 'Space Mono', size: 9 } }, grid: { color: '#f1f5f9' } },
              x: { ticks: { font: { family: 'Space Mono', size: 9 } }, grid: { display: false } }
            }
          }} />
        </div>
      </div>

      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} title="Audit Finding">
        <div className="modal-body">{modalMismatch ? generateAuditText(modalMismatch) : 'Loading...'}</div>
      </Modal>
    </div>
  );
}

