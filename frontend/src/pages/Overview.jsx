import { useEffect, useRef } from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Doughnut } from 'react-chartjs-2';
import { MISMATCHES, MISMATCH_TYPE_BREAKDOWN } from '../data/mockData';
import { inr, riskColor, mismatchIcon } from '../utils/formatters';
import Modal from '../components/ui/Modal';
import { useState } from 'react';
import { generateAuditText } from '../utils/auditGenerator';

ChartJS.register(ArcElement, Tooltip, Legend);

export default function Overview() {
  const [modalOpen, setModalOpen] = useState(false);
  const [modalId, setModalId] = useState(null);

  const criticals = MISMATCHES.filter(m => m.risk_level === 'CRITICAL');
  const maxCount = Math.max(...MISMATCH_TYPE_BREAKDOWN.map(t => t.count));
  const modalMismatch = MISMATCHES.find(x => x.id === modalId);

  function openModal(id) { setModalId(id); setModalOpen(true); }

  const donutData = {
    labels: ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'],
    datasets: [{
      data: [15, 42, 30, 13],
      backgroundColor: ['#ef4444', '#f97316', '#eab308', '#22c55e'],
      borderWidth: 2,
      borderColor: '#fff',
    }],
  };

  return (
    <div>
      <div className="kpi-grid">
        <div className="kpi-card" style={{ animationDelay: '.05s' }}>
          <div className="kpi-label">Total ITC at Risk</div>
          <div className="kpi-val kpi-critical">₹16,45,800</div>
          <div className="kpi-sub">Across 150 mismatch events</div>
        </div>
        <div className="kpi-card" style={{ animationDelay: '.1s' }}>
          <div className="kpi-label">Mismatches Detected</div>
          <div className="kpi-val">150</div>
          <div className="kpi-sub">30% of 500 invoices</div>
        </div>
        <div className="kpi-card" style={{ animationDelay: '.15s' }}>
          <div className="kpi-label">Knowledge Graph Nodes</div>
          <div className="kpi-val kpi-accent">245</div>
          <div className="kpi-sub">618 edges mapped</div>
        </div>
        <div className="kpi-card" style={{ animationDelay: '.2s' }}>
          <div className="kpi-label">Overall Match Rate</div>
          <div className="kpi-val" style={{ color: 'var(--low)' }}>70.0%</div>
          <div className="kpi-sub">Target ≥ 95%</div>
        </div>
      </div>

      <div className="two-col">
        <div className="card" style={{ animationDelay: '.25s' }}>
          <div className="card-title">Mismatch Category Breakdown</div>
          {MISMATCH_TYPE_BREAKDOWN.map(t => (
            <div key={t.type} style={{ marginBottom: '10px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                <span style={{ fontSize: '11px', fontWeight: 600 }}>{mismatchIcon(t.type)} {t.type}</span>
                <span style={{ fontSize: '10px', fontFamily: "'Space Mono',monospace", color: riskColor(t.risk_level) }}>{t.count} · {inr(t.itc_at_risk)}</span>
              </div>
              <div className="prog-bar">
                <div className={`prog-fill prog-${t.risk_level.toLowerCase()}`} style={{ width: `${(t.count / maxCount * 100).toFixed(0)}%` }} />
              </div>
            </div>
          ))}
        </div>
        <div className="card" style={{ animationDelay: '.3s' }}>
          <div className="card-title">Risk Level Distribution</div>
          <Doughnut data={donutData} options={{ responsive: true, plugins: { legend: { position: 'bottom', labels: { font: { family: 'Sora' }, padding: 12 } } } }} />
        </div>
      </div>

      <div className="card" style={{ animationDelay: '.35s', marginBottom: '24px' }}>
        <div className="card-title">🔴 Critical Alerts — Immediate Action Required</div>
        {criticals.map(m => (
          <div key={m.id} className="alert-item">
            <div className="pulse-dot" />
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '12px', fontWeight: 600 }}>{m.invoice_no} · {m.mismatch_type}</div>
              <div style={{ fontSize: '11px', color: '#b91c1c', marginTop: '2px' }}>{m.root_cause}</div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: "'Space Mono',monospace" }}>{m.supplier_gstin} · {inr(m.itc_at_risk)} at risk</div>
            </div>
            <button className="btn btn-outline" style={{ fontSize: '10px', padding: '5px 10px' }} onClick={() => openModal(m.id)}>View Audit</button>
          </div>
        ))}
      </div>

      <div className="card" style={{ animationDelay: '.4s' }}>
        <div className="card-title">Period Summary — Q4 2024</div>
        <div className="period-cards">
          <div className="period-card">
            <div className="period-month">October 2024</div>
            <div className="period-rate" style={{ color: 'var(--medium)' }}>72%</div>
            <div className="kpi-sub">38 mismatches · ₹4.8L at risk</div>
            <div className="prog-bar" style={{ marginTop: '8px' }}><div className="prog-fill prog-medium" style={{ width: '72%' }} /></div>
          </div>
          <div className="period-card">
            <div className="period-month">November 2024</div>
            <div className="period-rate" style={{ color: 'var(--high)' }}>68%</div>
            <div className="kpi-sub">51 mismatches · ₹6.2L at risk</div>
            <div className="prog-bar" style={{ marginTop: '8px' }}><div className="prog-fill prog-high" style={{ width: '68%' }} /></div>
          </div>
          <div className="period-card">
            <div className="period-month">December 2024</div>
            <div className="period-rate" style={{ color: 'var(--low)' }}>75%</div>
            <div className="kpi-sub">31 mismatches · ₹3.6L at risk</div>
            <div className="prog-bar" style={{ marginTop: '8px' }}><div className="prog-fill prog-low" style={{ width: '75%' }} /></div>
          </div>
        </div>
      </div>

      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} title="Audit Finding">
        <div className="modal-body">{modalMismatch ? generateAuditText(modalMismatch) : 'Loading...'}</div>
      </Modal>
    </div>
  );
}
