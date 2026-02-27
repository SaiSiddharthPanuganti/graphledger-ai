import { useEffect, useRef } from 'react';
import { GRAPH_NODES, GRAPH_EDGES } from '../data/mockData';

export default function GraphExplorer() {
  const svgRef = useRef(null);

  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;
    const nodeMap = {};
    GRAPH_NODES.forEach(n => nodeMap[n.id] = n);

    // Clear
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    const ns = 'http://www.w3.org/2000/svg';
    const defs = document.createElementNS(ns, 'defs');
    const marker = document.createElementNS(ns, 'marker');
    marker.setAttribute('id', 'arr');
    marker.setAttribute('viewBox', '0 0 10 10');
    marker.setAttribute('refX', '15');
    marker.setAttribute('refY', '5');
    marker.setAttribute('markerWidth', '6');
    marker.setAttribute('markerHeight', '6');
    marker.setAttribute('orient', 'auto');
    const path = document.createElementNS(ns, 'path');
    path.setAttribute('d', 'M 0 0 L 10 5 L 0 10 z');
    path.setAttribute('fill', '#4a5568');
    marker.appendChild(path);
    defs.appendChild(marker);
    svg.appendChild(defs);

    GRAPH_EDGES.forEach(e => {
      const s = nodeMap[e.from], t = nodeMap[e.to];
      if (!s || !t) return;
      const line = document.createElementNS(ns, 'line');
      line.setAttribute('x1', s.x); line.setAttribute('y1', s.y);
      line.setAttribute('x2', t.x); line.setAttribute('y2', t.y);
      line.setAttribute('stroke', '#4a5568'); line.setAttribute('stroke-width', '1.5');
      line.setAttribute('marker-end', 'url(#arr)'); line.setAttribute('opacity', '.7');
      svg.appendChild(line);
    });

    GRAPH_NODES.forEach(n => {
      if (n.type === 'Mismatch') {
        const rect = document.createElementNS(ns, 'rect');
        rect.setAttribute('x', n.x - 22); rect.setAttribute('y', n.y - 12);
        rect.setAttribute('width', '44'); rect.setAttribute('height', '24');
        rect.setAttribute('rx', '4'); rect.setAttribute('fill', '#ef4444'); rect.setAttribute('opacity', '.85');
        svg.appendChild(rect);
        const label = n.label.split('\n')[0];
        const txt = document.createElementNS(ns, 'text');
        txt.setAttribute('x', n.x); txt.setAttribute('y', n.y + 4);
        txt.setAttribute('text-anchor', 'middle'); txt.setAttribute('fill', '#fff');
        txt.setAttribute('font-size', '8');
        txt.textContent = label;
        svg.appendChild(txt);
      } else {
        const risk = n.risk || 0;
        const fill = risk > 65 ? '#ef4444' : risk > 45 ? '#f97316' : '#22c55e';
        const circle = document.createElementNS(ns, 'circle');
        circle.setAttribute('cx', n.x); circle.setAttribute('cy', n.y); circle.setAttribute('r', '22');
        circle.setAttribute('fill', fill); circle.setAttribute('opacity', '.85');
        svg.appendChild(circle);
        const score = document.createElementNS(ns, 'text');
        score.setAttribute('x', n.x); score.setAttribute('y', n.y + 4);
        score.setAttribute('text-anchor', 'middle'); score.setAttribute('fill', '#fff');
        score.setAttribute('font-size', '10'); score.setAttribute('font-weight', 'bold');
        score.textContent = risk;
        svg.appendChild(score);
        const lbl = document.createElementNS(ns, 'text');
        lbl.setAttribute('x', n.x); lbl.setAttribute('y', n.y + 36);
        lbl.setAttribute('text-anchor', 'middle'); lbl.setAttribute('fill', '#94a3b8');
        lbl.setAttribute('font-size', '8');
        lbl.textContent = n.name.substring(0, 14);
        svg.appendChild(lbl);
      }
    });
  }, []);

  return (
    <div>
      <div className="two-col" style={{ alignItems: 'start' }}>
        <div className="card">
          <div className="card-title">Knowledge Graph Visualization</div>
          <div className="graph-svg-wrap">
            <svg ref={svgRef} width="100%" height="380" viewBox="0 0 700 380" />
          </div>
          <div style={{ display: 'flex', gap: '12px', marginTop: '10px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '10px', display: 'flex', alignItems: 'center', gap: '4px' }}><span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#ef4444', display: 'inline-block' }} />Critical (&gt;65)</span>
            <span style={{ fontSize: '10px', display: 'flex', alignItems: 'center', gap: '4px' }}><span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#f97316', display: 'inline-block' }} />High (45–65)</span>
            <span style={{ fontSize: '10px', display: 'flex', alignItems: 'center', gap: '4px' }}><span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#22c55e', display: 'inline-block' }} />Low/Med (&lt;45)</span>
            <span style={{ fontSize: '10px', display: 'flex', alignItems: 'center', gap: '4px' }}><span style={{ width: '10px', height: '10px', borderRadius: '4px', background: '#ef4444', display: 'inline-block' }} />Mismatch Node</span>
          </div>
        </div>
        <div>
          <div className="card" style={{ marginBottom: '16px' }}>
            <div className="card-title">Graph Statistics</div>
            <div className="stat-row"><span className="stat-label" style={{ color: 'var(--text-muted)' }}>Nodes</span><span className="mono">245</span></div>
            <div className="stat-row" style={{ marginTop: '6px' }}><span className="stat-label" style={{ color: 'var(--text-muted)' }}>Edges</span><span className="mono">618</span></div>
            <div className="stat-row" style={{ marginTop: '6px' }}><span className="stat-label" style={{ color: 'var(--text-muted)' }}>Avg Degree</span><span className="mono">5.04</span></div>
            <div className="stat-row" style={{ marginTop: '6px' }}><span className="stat-label" style={{ color: 'var(--text-muted)' }}>Connected Components</span><span className="mono">8</span></div>
            <div className="stat-row" style={{ marginTop: '6px' }}><span className="stat-label" style={{ color: 'var(--text-muted)' }}>Risk Clusters</span><span className="mono">3</span></div>
            <div className="stat-row" style={{ marginTop: '6px' }}><span className="stat-label" style={{ color: 'var(--text-muted)' }}>Circular Patterns</span><span className="mono" style={{ color: 'var(--critical)' }}>1 detected</span></div>
          </div>
          <div className="cypher-panel">
            <div className="card-title" style={{ color: '#94a3b8', marginBottom: '10px' }}>⌨ Sample Cypher Queries</div>
            <div className="cypher-title">// 1. Multi-hop ITC chain validation</div>
            <div className="cypher-query">{`MATCH path=(g:GSTIN)-[:SUPPLIER_OF]->(i:Invoice)
  -[:HAS_MISMATCH]->(m:MismatchEvent)
WHERE m.risk_level = 'CRITICAL'
RETURN g.gstin, i.invoice_no, m.mismatch_type
ORDER BY m.amount_at_risk DESC LIMIT 10`}</div>
            <div className="cypher-title">// 2. Circular trading detection</div>
            <div className="cypher-query">{`MATCH cycle=(g1:GSTIN)-[:TRANSACTS_WITH*2..4]->(g1)
WHERE length(cycle) > 2
RETURN nodes(cycle) AS ring,
       reduce(v=0,r IN relationships(cycle)|
              v + r.total_value) AS ring_value`}</div>
            <div className="cypher-title">// 3. Non-filer vendor risk</div>
            <div className="cypher-query">{`MATCH (g:GSTIN)-[:FILED]->(r:Return)
WHERE r.return_type='GSTR1'
  AND r.status='PENDING'
  AND r.return_period > '012024'
RETURN g.gstin, count(r) AS missed_filings
ORDER BY missed_filings DESC`}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
