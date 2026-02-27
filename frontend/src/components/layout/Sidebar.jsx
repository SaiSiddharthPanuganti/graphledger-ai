import { NavLink } from 'react-router-dom';

const NAV_ITEMS = [
  { icon: '📊', label: 'Overview', path: '/' },
  { icon: '🔍', label: 'Reconciliation', path: '/recon' },
  { icon: '🔗', label: 'ITC Chain', path: '/chain' },
  { icon: '🏢', label: 'Vendor Risk', path: '/vendor' },
  { icon: '📋', label: 'Audit Trail', path: '/audit' },
  { icon: '🔍', label: 'OCR Upload', path: '/ocr' },
  { icon: '🧮', label: 'ITC Calculator', path: '/itc-calc' },
  { icon: '🤖', label: 'Predictions', path: '/predict' },
  { icon: '🕸', label: 'Graph Explorer', path: '/graph' },
  { icon: '⚡', label: 'Live Traversal', path: '/traversal' },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="brand">🏦 GraphLedger AI</div>
        <div className="sub">GST ITC Risk Intelligence v2.0</div>
      </div>
      <nav>
        {NAV_ITEMS.map(item => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
          >
            <span className="icon">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-stats">
        <div className="sidebar-stats-title">Graph Stats</div>
        <div className="stat-row"><span className="stat-label">Total Nodes</span><span className="stat-val">245</span></div>
        <div className="stat-row"><span className="stat-label">Total Edges</span><span className="stat-val">618</span></div>
        <div className="stat-row"><span className="stat-label">Vendors</span><span className="stat-val">50</span></div>
        <div className="stat-row"><span className="stat-label">Mismatches</span><span className="stat-val">150</span></div>
        <div className="stat-row"><span className="stat-label">Invoices</span><span className="stat-val">500</span></div>
        <div className="stat-row"><span className="stat-label">Match Rate</span><span className="stat-val" style={{ color: 'var(--amber)' }}>70.0%</span></div>
      </div>
      <div className="sidebar-footer">Powered by GraphLedger AI · NetworkX</div>
    </aside>
  );
}
