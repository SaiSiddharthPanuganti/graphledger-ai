import { useState } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement, PointElement, Filler, Tooltip, Legend } from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import { MISMATCHES } from '../data/mockData';
import { inr, mismatchIcon } from '../utils/formatters';
import RiskBadge from '../components/ui/RiskBadge';
import StatusBadge from '../components/ui/StatusBadge';
import Modal from '../components/ui/Modal';
import { generateAuditText } from '../utils/auditGenerator';

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, Filler, Tooltip, Legend);

export default function Reconciliation() {
  const [search, setSearch] = useState('');
  const [riskFilter, setRiskFilter] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [modalId, setModalId] = useState(null);

  const filtered = MISMATCHES.filter(m => {
    const matchSearch = !search || m.invoice_no.toLowerCase().includes(search) || m.supplier_gstin.toLowerCase().includes(search);
    const matchRisk = !riskFilter || m.risk_level === riskFilter;
    return matchSearch && matchRisk;
  });

  const modalMismatch = MISMATCHES.find(x => x.id === modalId);

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
              <tr key={m.id}>
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
