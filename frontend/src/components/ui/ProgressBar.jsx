export default function ProgressBar({ value, colorClass = 'prog-amber' }) {
  return (
    <div className="prog-bar">
      <div className={`prog-fill ${colorClass}`} style={{ width: `${value}%` }} />
    </div>
  );
}
