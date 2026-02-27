export default function RiskBadge({ risk }) {
  return <span className={`badge badge-${risk.toLowerCase()}`}>{risk}</span>;
}
