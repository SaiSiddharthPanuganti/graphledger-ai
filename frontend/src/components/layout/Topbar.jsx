import { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { MISMATCHES } from '../../data/mockData';
import { inr } from '../../utils/formatters';
import { PAGE_EXPORTERS } from '../../utils/exportUtils';

export default function Topbar({ title }) {
  const [loading, setLoading] = useState(false);
  const location = useLocation();

  function runRecon() {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      alert('✅ Reconciliation complete!\n\nPeriod: Q4 2024\n• Invoices processed: 500\n• Mismatches detected: 150\n• ITC at risk: ₹16,45,800\n• Critical findings: 15');
    }, 2000);
  }

  function handleExport() {
    const exporter = PAGE_EXPORTERS[location.pathname];
    if (exporter) {
      exporter();
    } else if (location.pathname === '/ocr') {
      // OCR page handles its own export internally
      document.dispatchEvent(new CustomEvent('ocr-export'));
    }
  }

  return (
    <div className="topbar">
      <h1>{title}</h1>
      <select className="period-select">
        <option>Q4 2024 (Oct–Dec)</option>
        <option>Q3 2024 (Jul–Sep)</option>
        <option>Q2 2024 (Apr–Jun)</option>
        <option>Q1 2024 (Jan–Mar)</option>
      </select>
      <button className="btn btn-amber" onClick={runRecon} disabled={loading}>
        {loading ? (
          <><span style={{ display: 'none' }}>▶ Run Recon</span><span className="loading-spin" /></>
        ) : (
          '▶ Run Recon'
        )}
      </button>
      <button className="btn btn-outline" onClick={handleExport}>⬇ Export</button>
    </div>
  );
}
