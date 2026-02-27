import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Tooltip, Legend } from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { ITC_CHAIN_HOPS } from '../data/mockData';
import { inr } from '../utils/formatters';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

export default function ITCChain() {
  const hopChartData = {
    labels: ['Hop 0', 'Hop 1', 'Hop 2', 'Hop 3', 'Hop 4'],
    datasets: [
      { label: 'ITC Eligible', data: [4520000, 1850000, 0, 430000, 210000], backgroundColor: 'rgba(34,197,94,.7)', borderRadius: 4 },
      { label: 'ITC Blocked', data: [0, 0, 980000, 0, 0], backgroundColor: 'rgba(239,68,68,.7)', borderRadius: 4 }
    ],
  };

  return (
    <div>
      <div className="three-col">
        <div className="kpi-card">
          <div className="kpi-label">Chain ITC Eligible</div>
          <div className="kpi-val kpi-accent">₹80,20,000</div>
          <div className="kpi-sub">4-hop supply chain</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Blocked at Source</div>
          <div className="kpi-val kpi-critical">₹9,80,000</div>
          <div className="kpi-sub">Hop 2 — INVOICE_MISSING_2B</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Chain Risk Level</div>
          <div className="kpi-val" style={{ color: 'var(--high)' }}>HIGH</div>
          <div className="kpi-sub">Section 16(2)(aa) exposure</div>
        </div>
      </div>

      <div className="two-col" style={{ alignItems: 'start' }}>
        <div className="card">
          <div className="card-title">Supply Chain ITC Traversal</div>
          {ITC_CHAIN_HOPS.map(h => {
            const cls = h.status === 'SAFE' ? 'hop-safe' : h.status === 'RISKY' ? 'hop-risky' : 'hop-warn';
            return (
              <div key={h.hop} className={`hop-node ${cls}`} style={{ marginLeft: h.hop * 20 + 'px' }}>
                <div className="hop-badge" style={{ background: h.color, color: '#fff' }}>H{h.hop}</div>
                <div className="hop-info">
                  <div className="hop-name">{h.name}</div>
                  <div className="hop-gstin">{h.gstin}</div>
                  <div className="hop-itc" style={{ color: h.color }}>{inr(h.itc_value)}</div>
                  <div className="hop-note">{h.note}</div>
                </div>
              </div>
            );
          })}
        </div>
        <div>
          <div className="card" style={{ marginBottom: '16px' }}>
            <div className="card-title">ITC Eligible vs Blocked per Hop</div>
            <Bar data={hopChartData} options={{
              responsive: true,
              plugins: { legend: { position: 'bottom', labels: { font: { family: 'Sora', size: 10 } } } },
              scales: {
                x: { stacked: true, ticks: { font: { family: 'Space Mono', size: 9 } }, grid: { display: false } },
                y: { stacked: true, ticks: { callback: v => '₹' + Math.round(v / 100000) + 'L', font: { family: 'Space Mono', size: 9 } }, grid: { color: '#f1f5f9' } }
              }
            }} />
          </div>
          <div className="legal-panel">
            <div className="card-title" style={{ color: '#94a3b8' }}>📜 Regulatory Citations</div>
            <div className="legal-item"><div className="legal-sec">Section 16(2)(aa) CGST Act</div>ITC admissible only if invoice appears in GSTR-2B of recipient</div>
            <div className="legal-item"><div className="legal-sec">Rule 36(4) CGST Rules</div>Provisional ITC capped at 105% of GSTR-2B eligible ITC</div>
            <div className="legal-item"><div className="legal-sec">Section 16(2)(c) CGST Act</div>ITC linked to supplier's actual tax deposit with government</div>
            <div className="legal-item"><div className="legal-sec">Section 122(1)(ii) CGST Act</div>Penalty for wrongful ITC availment — 100% of tax involved</div>
          </div>
        </div>
      </div>
    </div>
  );
}
