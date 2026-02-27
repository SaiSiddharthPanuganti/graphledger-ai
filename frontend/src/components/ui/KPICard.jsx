export default function KPICard({ label, value, sub, valueClass = '', style = {}, delay = 0 }) {
  return (
    <div className="kpi-card" style={{ animationDelay: `${delay}s`, ...style }}>
      <div className="kpi-label">{label}</div>
      <div className={`kpi-val ${valueClass}`}>{value}</div>
      <div className="kpi-sub">{sub}</div>
    </div>
  );
}
