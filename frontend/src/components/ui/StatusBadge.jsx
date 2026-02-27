export default function StatusBadge({ status }) {
  const cls = status === 'RESOLVED' ? 'badge-resolved' : status === 'IN_PROGRESS' ? 'badge-progress' : 'badge-pending';
  return <span className={`badge ${cls}`}>{status}</span>;
}
