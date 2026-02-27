import { useState } from 'react';
import { MISMATCHES } from '../data/mockData';
import { mismatchIcon } from '../utils/formatters';
import { generateAuditText } from '../utils/auditGenerator';
import RiskBadge from '../components/ui/RiskBadge';

export default function AuditTrail() {
  const [selectedId, setSelectedId] = useState(null);
  const selected = MISMATCHES.find(x => x.id === selectedId);
  const auditText = selected ? generateAuditText(selected) : 'Select a mismatch from the list to view the audit finding...';

  function copyAudit() {
    const txt = selected ? generateAuditText(selected) : '';
    navigator.clipboard?.writeText(txt).then(() => alert('Audit text copied to clipboard!'));
  }

  function downloadAudit() {
    const txt = selected ? generateAuditText(selected) : '';
    const fname = selected ? `audit-${selected.invoice_no}.txt` : 'audit-finding.txt';
    const blob = new Blob([txt], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = fname;
    a.click();
  }

  return (
    <div className="audit-layout">
      <div className="audit-list">
        {MISMATCHES.map(m => (
          <div
            key={m.id}
            className={`audit-list-item${selectedId === m.id ? ' selected' : ''}`}
            onClick={() => setSelectedId(m.id)}
          >
            <div className="mis-id">{m.id}</div>
            <div className="mis-inv">{m.invoice_no}</div>
            <div className="mis-type">{mismatchIcon(m.mismatch_type)} {m.mismatch_type}</div>
            <div style={{ marginTop: '4px' }}><RiskBadge risk={m.risk_level} /></div>
          </div>
        ))}
      </div>
      <div className="audit-panel">
        <div className="audit-panel-header">
          <span>● AUDIT FINDING — GraphLedger AI Engine v2.0</span>
          <div className="audit-panel-btns">
            <button className="term-btn" onClick={copyAudit}>⎘ Copy</button>
            <button className="term-btn" onClick={downloadAudit}>⬇ Download</button>
          </div>
        </div>
        <div className="audit-content">{auditText}</div>
      </div>
    </div>
  );
}
