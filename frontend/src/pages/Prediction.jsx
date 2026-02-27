import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Tooltip, Legend } from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { PREDICTIONS, VENDORS } from '../data/mockData';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

const RISK_FACTORS = [
  { label: 'Mismatch Ratio', weight: 35, color: '#ef4444' },
  { label: 'Filing Behavior', weight: 25, color: '#f97316' },
  { label: 'Network Contagion', weight: 20, color: '#eab308' },
  { label: 'Critical Mismatches', weight: 15, color: '#8b5cf6' },
  { label: 'Transaction Volume', weight: 5, color: '#22c55e' },
];

export default function Prediction() {
  const cats = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
  const currCounts = cats.map(c => PREDICTIONS.filter(p => { const v = VENDORS.find(x => x.gstin === p.gstin); return v && v.risk_category === c; }).length);
  const predCounts = cats.map(c => PREDICTIONS.filter(p => {
    const s = p.predicted;
    const cat = s >= 80 ? 'CRITICAL' : s >= 60 ? 'HIGH' : s >= 40 ? 'MEDIUM' : 'LOW';
    return cat === c;
  }).length);

  const predGroupData = {
    labels: cats,
    datasets: [
      { label: 'Current', data: currCounts, backgroundColor: 'rgba(99,102,241,.7)', borderRadius: 4 },
      { label: 'Predicted', data: predCounts, backgroundColor: 'rgba(245,158,11,.7)', borderRadius: 4 },
    ],
  };

  const top3 = PREDICTIONS.filter(p => p.trend === 'up').slice(0, 3);

  return (
    <div>
      <div className="two-col" style={{ alignItems: 'start' }}>
        <div className="card">
          <div className="card-title">Next Period Risk Forecast</div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
            <thead>
              <tr style={{ background: '#f8fafc' }}>
                <th style={{ padding: '8px 10px', textAlign: 'left', fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', borderBottom: '1px solid var(--border)' }}>Vendor</th>
                <th style={{ padding: '8px 10px', fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', borderBottom: '1px solid var(--border)' }}>Current</th>
                <th style={{ padding: '8px 10px', fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', borderBottom: '1px solid var(--border)' }}>Predicted</th>
                <th style={{ padding: '8px 10px', fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', borderBottom: '1px solid var(--border)' }}>Trend</th>
              </tr>
            </thead>
            <tbody>
              {PREDICTIONS.map(p => {
                const trendColor = p.trend === 'up' ? '#ef4444' : p.trend === 'down' ? '#22c55e' : '#94a3b8';
                const trendArrow = p.trend === 'up' ? '↑' : p.trend === 'down' ? '↓' : '→';
                const delta = p.predicted - p.current;
                const deltaStr = (delta > 0 ? '+' : '') + delta.toFixed(0);
                return (
                  <tr key={p.gstin}>
                    <td style={{ padding: '8px 10px' }}>
                      {p.name}
                      <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: "'Space Mono',monospace" }}>{p.gstin}</div>
                    </td>
                    <td style={{ padding: '8px 10px', fontFamily: "'Space Mono',monospace", fontSize: '12px' }}>{p.current}</td>
                    <td style={{ padding: '8px 10px', fontFamily: "'Space Mono',monospace", fontSize: '12px', fontWeight: 700, color: trendColor }}>{p.predicted}</td>
                    <td style={{ padding: '8px 10px', fontSize: '14px', fontWeight: 700, color: trendColor }}>
                      {trendArrow} <span style={{ fontSize: '11px' }}>{deltaStr}</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div>
          <div className="card" style={{ marginBottom: '16px' }}>
            <div className="card-title">Risk Factor Weights</div>
            {RISK_FACTORS.map(f => (
              <div key={f.label} style={{ marginBottom: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                  <span style={{ fontSize: '11px', fontWeight: 600 }}>{f.label}</span>
                  <span style={{ fontSize: '11px', fontFamily: "'Space Mono',monospace" }}>{f.weight}%</span>
                </div>
                <div className="prog-bar">
                  <div className="prog-fill" style={{ width: `${f.weight * 2}%`, background: f.color }} />
                </div>
              </div>
            ))}
          </div>
          <div className="card">
            <div className="card-title">Current vs Predicted Categories</div>
            <Bar data={predGroupData} options={{
              responsive: true,
              plugins: { legend: { position: 'bottom', labels: { font: { family: 'Sora', size: 10 } } } },
              scales: {
                x: { ticks: { font: { family: 'Space Mono', size: 9 } }, grid: { display: false } },
                y: { ticks: { stepSize: 1, font: { family: 'Space Mono', size: 9 } }, grid: { color: '#f1f5f9' } }
              }
            }} />
          </div>
        </div>
      </div>

      <div className="card" style={{ marginTop: '20px' }}>
        <div className="card-title">🤖 AI Graph Intelligence Insights</div>
        {top3.map(p => (
          <div key={p.gstin} className="insight-card">
            <div className="insight-vendor">🤖 {p.name} ({p.gstin})</div>
            <div className="insight-text">
              Graph analysis predicts this vendor's risk score will increase from{' '}
              <strong style={{ color: '#f59e0b' }}>{p.current}</strong> to{' '}
              <strong style={{ color: '#ef4444' }}>{p.predicted}</strong> next period.
              Primary drivers: {p.factors.join('; ')}.
              Network contagion analysis shows connected vendors averaging 65+ risk score,
              contributing additional exposure via Section 16(2)(c) propagation pathway.
            </div>
            <div className="insight-action">
              Recommended Action: {p.predicted >= 80
                ? '⛔ Proactively restrict ITC. Initiate vendor audit under Section 65 CGST Act.'
                : '⚠️ Enhanced monitoring. Request compliance certificate before next supply.'}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
