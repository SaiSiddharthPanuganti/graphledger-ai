import { useState } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Tooltip, Legend } from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { VENDORS } from '../data/mockData';
import { inr, riskColor } from '../utils/formatters';
import RiskBadge from '../components/ui/RiskBadge';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

export default function VendorRisk() {
  const [catFilter, setCatFilter] = useState('');

  const filtered = catFilter ? VENDORS.filter(v => v.risk_category === catFilter) : VENDORS;

  const vendorBarData = {
    labels: VENDORS.map(v => v.name.substring(0, 15)),
    datasets: [{
      label: 'Risk Score',
      data: VENDORS.map(v => v.risk_score),
      backgroundColor: VENDORS.map(v => riskColor(v.risk_category)),
      borderRadius: 4,
    }],
  };

  return (
    <div>
      <div className="filter-bar">
        <select className="filter-sel" value={catFilter} onChange={e => setCatFilter(e.target.value)}>
          <option value="">All Categories</option>
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
              <th>Risk</th><th>Vendor / GSTIN</th><th>Sector / State</th>
              <th>Mismatches</th><th>ITC at Risk</th><th>Filing Streak</th>
              <th>Category</th><th>Recommendation</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(v => {
              const col = riskColor(v.risk_category);
              return (
                <tr key={v.gstin}>
                  <td><div className="risk-circle" style={{ background: col }}>{v.risk_score}</div></td>
                  <td>
                    <div style={{ fontSize: '12px', fontWeight: 600 }}>{v.name}</div>
                    <div className="mono" style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{v.gstin}</div>
                  </td>
                  <td>
                    <div style={{ fontSize: '11px' }}>{v.sector}</div>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{v.state}</div>
                  </td>
                  <td className="mono" style={{ color: col }}>{v.mismatch_count}</td>
                  <td className="mono" style={{ color: 'var(--critical)' }}>{inr(v.itc_at_risk)}</td>
                  <td style={{ minWidth: '100px' }}>
                    <div style={{ fontSize: '10px', marginBottom: '3px' }}>{v.filing_streak}/24 months</div>
                    <div className="prog-bar">
                      <div className={`prog-fill prog-${v.risk_category.toLowerCase()}`} style={{ width: `${(v.filing_streak / 24 * 100).toFixed(0)}%` }} />
                    </div>
                  </td>
                  <td><RiskBadge risk={v.risk_category} /></td>
                  <td style={{ fontSize: '10px', color: 'var(--text-muted)', maxWidth: '140px' }}>{v.rec}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="two-col">
        <div className="card">
          <div className="card-title">Vendor Risk Scores</div>
          <Bar data={vendorBarData} options={{
            indexAxis: 'y',
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
              x: { max: 100, ticks: { font: { family: 'Space Mono', size: 9 } }, grid: { color: '#f1f5f9' } },
              y: { ticks: { font: { family: 'Sora', size: 10 } }, grid: { display: false } }
            }
          }} />
        </div>
        <div className="card">
          <div className="card-title">⚠️ Contagion Risk Network</div>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '12px' }}>
            Circular trading pattern detected between 3 vendors. Risk propagation risk under Section 16(2)(c).
          </p>
          <div className="contagion-alert">
            <div className="contagion-title">🔴 Circular Trading Ring Detected</div>
            <div className="contagion-path">Mahindra Castings → Flex Systems → Gujarat Agro → Mahindra Castings</div>
            <div style={{ fontSize: '11px', color: '#b91c1c', marginTop: '6px' }}>ITC at risk: ₹3,85,400 · Refer to Section 132 CGST Act</div>
          </div>
        </div>
      </div>
    </div>
  );
}
