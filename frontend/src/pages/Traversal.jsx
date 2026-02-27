import { useEffect, useRef, useState, useCallback } from 'react';
import * as d3 from 'd3';
import { NODES, LINKS, ITC_STEPS, GSTR_STEPS, FRAUD_STEPS } from '../data/mockData';

function nodeColor(d) {
  if (d.hop === 0) return '#6366f1';
  if (d.status === 'BLOCKED') return '#ef4444';
  if (d.risk >= 70) return '#ef4444';
  if (d.risk >= 50) return '#f97316';
  if (d.risk >= 35) return '#eab308';
  return '#22c55e';
}
function linkColor(type) {
  if (type === 'HAS_MISMATCH') return '#ef4444';
  if (type === 'CIRCULAR') return '#a855f7';
  if (type === 'FILED') return '#3b82f6';
  if (type === 'REFLECTED') return '#22c55e';
  return '#334155';
}
function getNodesForMode(mode) {
  if (mode === 'gstr') return NODES.filter(n => !n.id.startsWith('m') && (n.hop <= 1 || n.id === 'n3' || n.id.startsWith('g')));
  if (mode === 'fraud') return NODES.filter(n => ['n1', 'n2', 'n3', 'm1', 'm2'].includes(n.id));
  return NODES.filter(n => !n.id.startsWith('g'));
}
function getLinksForMode(mode) {
  if (mode === 'fraud') return LINKS.filter(l => l.type === 'CIRCULAR' || l.type === 'HAS_MISMATCH').filter(l => {
    const srcs = ['n1', 'n2', 'n3', 'm1', 'm2'];
    return srcs.includes(l.source.id || l.source) && srcs.includes(l.target.id || l.target);
  });
  if (mode === 'gstr') return LINKS.filter(l => l.type === 'FILED' || l.type === 'REFLECTED' || l.type === 'PURCHASED').filter(l => {
    const ns = getNodesForMode('gstr').map(n => n.id);
    return ns.includes(l.source.id || l.source) && ns.includes(l.target.id || l.target);
  });
  return LINKS.filter(l => l.type === 'PURCHASED' || l.type === 'HAS_MISMATCH');
}
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

export default function Traversal() {
  const svgRef = useRef(null);
  const tooltipRef = useRef(null);
  const nodeInfoRef = useRef(null);
  const stepLabelRef = useRef(null);
  const kpiEligibleRef = useRef(null);
  const kpiBlockedRef = useRef(null);
  const kpiHopsRef = useRef(null);
  const kpiStatusRef = useRef(null);
  const btnPlayRef = useRef(null);

  const [mode, setMode] = useState('itc');
  const [logEntries, setLogEntries] = useState([{ ts: '--:--:--', cls: 'log-info', msg: 'System ready. Select a mode and click Run.' }]);
  const [stepDots, setStepDots] = useState([]);

  // D3 refs — kept in refs not state to avoid re-renders
  const simRef = useRef(null);
  const svgSelRef = useRef(null);
  const nodeGRef = useRef(null);
  const linkGRef = useRef(null);
  const particleLayerRef = useRef(null);
  const labelGRef = useRef(null);
  const particleDataRef = useRef([]);
  const animIdRef = useRef(null);
  const animRunningRef = useRef(false);
  const animatingRef = useRef(false);
  const visitedRef = useRef(new Set());
  const blockedRef = useRef(new Set());
  const modeRef = useRef('itc');
  const speedRangeRef = useRef(null);
  const inited = useRef(false);

  function getSpeed() {
    return 6 - parseInt(speedRangeRef.current?.value || '3');
  }

  function addLog(msg, type = 'info') {
    const cls = { info: 'log-info', ok: 'log-ok', warn: 'log-warn', crit: 'log-crit', hop: 'log-hop' }[type] || 'log-info';
    const ts = new Date().toLocaleTimeString('en-IN', { hour12: false });
    setLogEntries(prev => [{ ts, cls, msg }, ...prev]);
  }

  function buildStepBar(m) {
    const steps = m === 'gstr' ? GSTR_STEPS : m === 'fraud' ? FRAUD_STEPS : ITC_STEPS;
    setStepDots(steps.map((_, i) => 'idle'));
  }

  function updateStepBar(idx) {
    const mode = modeRef.current;
    const steps = mode === 'gstr' ? GSTR_STEPS : mode === 'fraud' ? FRAUD_STEPS : ITC_STEPS;
    setStepDots(steps.map((_, i) => i < idx ? 'done' : i === idx ? 'active' : 'idle'));
    if (stepLabelRef.current) {
      stepLabelRef.current.textContent = idx < steps.length ? `Step ${idx + 1} of ${steps.length}` : 'Traversal complete';
    }
  }

  function highlightNode(id, color, glow = true) {
    const g = d3.select('#node-' + id);
    g.select('circle.node-circle')
      .transition().duration(400)
      .attr('stroke', color).attr('stroke-width', 3.5).attr('fill-opacity', .35)
      .attr('filter', glow ? 'url(#glow)' : null);
    g.select('circle.node-inner')
      .transition().duration(400).attr('fill', color).attr('fill-opacity', .15);
  }

  function pulseNode(id) {
    const g = d3.select('#node-' + id).select('circle.node-circle');
    function doPulse() {
      g.transition().duration(600).attr('r', 26).attr('fill-opacity', .45)
        .transition().duration(600).attr('r', 22).attr('fill-opacity', .2)
        .on('end', doPulse);
    }
    doPulse();
  }

  function flashNode(id, color) {
    const g = d3.select('#node-' + id).select('circle.node-circle');
    g.transition().duration(200).attr('fill', color).attr('fill-opacity', .6)
      .transition().duration(400).attr('fill', color).attr('fill-opacity', .2);
  }

  function highlightLink(sourceId, targetId, color) {
    linkGRef.current?.selectAll('line').each(function (d) {
      const sid = d.source.id || d.source, tid = d.target.id || d.target;
      if (sid === sourceId && tid === targetId) {
        d3.select(this).transition().duration(300)
          .attr('stroke', color).attr('stroke-opacity', .9).attr('stroke-width', 3)
          .attr('marker-end', 'url(#arr-active)');
      }
    });
  }

  function dimUnvisited() {
    nodeGRef.current?.selectAll('g.node').each(function (d) {
      if (d.type === 'GSTIN' && !visitedRef.current.has(d.id)) {
        d3.select(this).select('circle.node-circle').transition().attr('fill-opacity', .06).attr('stroke-opacity', .2);
        d3.select(this).select('circle.node-inner').transition().attr('fill-opacity', .03);
      }
    });
  }

  function resetNodeStyles() {
    nodeGRef.current?.selectAll('g.node').each(function (d) {
      const g = d3.select(this);
      g.select('circle.node-circle').interrupt().transition().duration(300)
        .attr('stroke', nodeColor(d)).attr('stroke-width', 2).attr('fill-opacity', .2)
        .attr('filter', null).attr('r', d.hop === 0 ? 30 : 22);
      g.select('circle.node-inner').interrupt().transition().duration(300)
        .attr('fill-opacity', .08).attr('fill', nodeColor(d));
    });
    linkGRef.current?.selectAll('line').transition().duration(300)
      .attr('stroke', d => linkColor(d.type)).attr('stroke-opacity', .35)
      .attr('stroke-width', d => d.type === 'CIRCULAR' ? 2.5 : d.type === 'HAS_MISMATCH' ? 1.5 : 2)
      .attr('marker-end', 'url(#arr-default)');
  }

  function spawnParticles(sourceId, targetId, color, count = 3) {
    const sNode = simRef.current?.nodes().find(n => n.id === sourceId);
    const tNode = simRef.current?.nodes().find(n => n.id === targetId);
    if (!sNode || !tNode) return;
    for (let i = 0; i < count; i++) {
      particleDataRef.current.push({
        sx: sNode.x, sy: sNode.y, tx: tNode.x, ty: tNode.y,
        progress: -(i * 0.2), color, size: 3.5, opacity: 1,
        id: Math.random()
      });
    }
  }

  function startParticleStream(pairs, color) {
    pairs.forEach(([s, t]) => spawnParticles(s, t, color, 4));
  }

  function animateParticles() {
    particleDataRef.current = particleDataRef.current.filter(p => p.progress < 1.2);
    particleDataRef.current.forEach(p => { p.progress += 0.008 * getSpeed(); });

    const circles = particleLayerRef.current?.selectAll('circle.particle')
      .data(particleDataRef.current.filter(p => p.progress >= 0 && p.progress <= 1), d => d.id);
    if (circles) {
      circles.enter().append('circle').attr('class', 'particle')
        .attr('r', d => d.size).attr('fill', d => d.color).attr('opacity', d => d.opacity);
      circles
        .attr('cx', d => d.sx + (d.tx - d.sx) * d.progress)
        .attr('cy', d => d.sy + (d.ty - d.sy) * d.progress)
        .attr('opacity', d => d.progress > 0.85 ? 1 - ((d.progress - 0.85) / 0.15) : 1);
      circles.exit().remove();
    }
    if (animRunningRef.current) animIdRef.current = requestAnimationFrame(animateParticles);
  }

  function drawLinks(links) {
    linkGRef.current?.selectAll('*').remove();
    const linkElements = linkGRef.current?.selectAll('line')
      .data(links).enter().append('line')
      .attr('class', d => 'link link-' + d.type)
      .attr('stroke', d => linkColor(d.type))
      .attr('stroke-width', d => d.type === 'CIRCULAR' ? 2.5 : d.type === 'HAS_MISMATCH' ? 1.5 : 2)
      .attr('stroke-dasharray', d => d.type === 'HAS_MISMATCH' ? '5,4' : d.type === 'FILED' ? '6,3' : null)
      .attr('stroke-opacity', .35)
      .attr('marker-end', 'url(#arr-default)');

    labelGRef.current?.selectAll('.link-label').remove();
    labelGRef.current?.selectAll('.link-label')
      .data(links.filter(l => l.label && l.type !== 'FILED' && l.type !== 'REFLECTED'))
      .enter().append('text').attr('class', 'link-label')
      .attr('font-size', 8).attr('fill', '#475569')
      .attr('text-anchor', 'middle').attr('font-family', 'Space Mono,monospace')
      .text(d => d.label);
  }

  function drawNodes(nodes) {
    nodeGRef.current?.selectAll('*').remove();
    const tooltip = tooltipRef.current;
    const ng = nodeGRef.current?.selectAll('g.node').data(nodes).enter().append('g')
      .attr('class', 'node').attr('id', d => 'node-' + d.id).style('cursor', 'pointer')
      .call(d3.drag()
        .on('start', (e, d) => { if (!e.active) simRef.current?.alphaTarget(.3).restart(); d.fx = d.x; d.fy = d.y; })
        .on('drag', (e, d) => { d.fx = e.x; d.fy = e.y; })
        .on('end', (e, d) => { if (!e.active) simRef.current?.alphaTarget(0); d.fx = null; d.fy = null; }))
      .on('mouseover', (e, d) => {
        showTooltip(d, e);
        if (nodeInfoRef.current) nodeInfoRef.current.innerHTML = nodeInfoHtml(d);
      })
      .on('mouseout', () => { if (tooltip) tooltip.style.opacity = '0'; });

    ng?.each(function (d) {
      const g = d3.select(this);
      if (d.type === 'MISMATCH') {
        g.append('rect').attr('x', -32).attr('y', -14).attr('width', 64).attr('height', 28)
          .attr('rx', 4).attr('fill', '#450a0a').attr('stroke', d.riskLevel === 'CRITICAL' ? '#ef4444' : '#f97316').attr('stroke-width', 1.5);
        g.append('text').attr('text-anchor', 'middle').attr('y', -2).attr('fill', '#fca5a5')
          .attr('font-size', 7).attr('font-family', 'Space Mono,monospace')
          .selectAll('tspan').data(d.label.split('\n')).enter().append('tspan')
          .attr('x', 0).attr('dy', (dd, i) => i === 0 ? 0 : 10).text(dd => dd);
      } else if (d.type === 'GSTR') {
        g.append('rect').attr('x', -30).attr('y', -16).attr('width', 60).attr('height', 32)
          .attr('rx', 6).attr('fill', d.filed ? '#0c2240' : '#2d0a0a')
          .attr('stroke', d.filed ? '#3b82f6' : '#ef4444').attr('stroke-width', 1.5)
          .attr('stroke-dasharray', d.filed ? null : '4,3');
        g.append('text').attr('text-anchor', 'middle').attr('y', -3).attr('fill', d.filed ? '#93c5fd' : '#fca5a5')
          .attr('font-size', 7).attr('font-family', 'Space Mono,monospace')
          .selectAll('tspan').data(d.label.split('\n')).enter().append('tspan')
          .attr('x', 0).attr('dy', (dd, i) => i === 0 ? 0 : 10).text(dd => dd);
      } else {
        const r = d.hop === 0 ? 30 : 22;
        g.append('circle').attr('r', r).attr('class', 'node-circle')
          .attr('fill', nodeColor(d)).attr('fill-opacity', .2)
          .attr('stroke', nodeColor(d)).attr('stroke-width', 2);
        g.append('circle').attr('r', r - 4).attr('class', 'node-inner')
          .attr('fill', nodeColor(d)).attr('fill-opacity', .08);
        g.append('text').attr('text-anchor', 'middle').attr('y', d.hop === 0 ? 5 : 4)
          .attr('fill', '#e2e8f0').attr('font-size', d.hop === 0 ? 13 : 11)
          .attr('font-weight', '700').attr('font-family', 'Space Mono,monospace')
          .text(d.hop === 0 ? 'HOP 0' : d.risk);
        g.append('text').attr('text-anchor', 'middle').attr('y', d.hop === 0 ? 50 : 40)
          .attr('fill', '#94a3b8').attr('font-size', d.hop === 0 ? 10 : 9)
          .attr('font-family', 'Sora,sans-serif').text(d.label);
        if (d.hop > 0) g.append('text').attr('text-anchor', 'middle').attr('y', -28)
          .attr('fill', '#475569').attr('font-size', 8).attr('font-family', 'Space Mono,monospace')
          .text('HOP ' + d.hop);
      }
    });
  }

  function showTooltip(d, event) {
    const tt = tooltipRef.current;
    if (!tt) return;
    if (d.type === 'MISMATCH') {
      tt.innerHTML = `<div class="anim-tt-title">${d.label.replace('\n', ' — ')}</div>
      <div class="anim-tt-row"><span class="anim-tt-key">Risk</span><span class="anim-tt-val" style="color:#ef4444">${d.riskLevel}</span></div>
      <div class="anim-tt-row"><span class="anim-tt-key">ITC at Risk</span><span class="anim-tt-val">₹${d.itc.toLocaleString('en-IN')}</span></div>
      <div class="anim-tt-row"><span class="anim-tt-key">Section</span><span class="anim-tt-val">16(2)(aa) CGST</span></div>`;
    } else if (d.type === 'GSTR') {
      tt.innerHTML = `<div class="anim-tt-title">${d.gstrType} — ${d.period}</div>
      <div class="anim-tt-row"><span class="anim-tt-key">Status</span><span class="anim-tt-val" style="color:${d.filed ? '#22c55e' : '#ef4444'}">${d.filed ? 'FILED' : 'NOT FILED'}</span></div>
      <div class="anim-tt-row"><span class="anim-tt-key">Period</span><span class="anim-tt-val">${d.period}</span></div>`;
    } else {
      tt.innerHTML = `<div class="anim-tt-title">${d.label}</div>
      <div class="anim-tt-row"><span class="anim-tt-key">GSTIN</span><span class="anim-tt-val">${d.gstin}</span></div>
      <div class="anim-tt-row"><span class="anim-tt-key">Risk Score</span><span class="anim-tt-val" style="color:${nodeColor(d)}">${d.risk}/100</span></div>
      <div class="anim-tt-row"><span class="anim-tt-key">Category</span><span class="anim-tt-val">${d.category}</span></div>
      <div class="anim-tt-row"><span class="anim-tt-key">ITC Value</span><span class="anim-tt-val">₹${(d.itc / 100000).toFixed(1)}L</span></div>
      <div class="anim-tt-row"><span class="anim-tt-key">Filing Streak</span><span class="anim-tt-val">${d.filingStreak} months</span></div>
      <div class="anim-tt-row"><span class="anim-tt-key">Mismatches</span><span class="anim-tt-val">${d.mismatches}</span></div>
      <div class="anim-tt-row"><span class="anim-tt-key">Hop</span><span class="anim-tt-val">${d.hop}</span></div>`;
    }
    const rect = svgRef.current?.closest('.trav-canvas')?.getBoundingClientRect();
    if (rect) {
      tt.style.left = (event.clientX - rect.left + 14) + 'px';
      tt.style.top = (event.clientY - rect.top - 20) + 'px';
      tt.style.opacity = '1';
    }
  }

  function nodeInfoHtml(d) {
    if (!d.gstin) return `<span style="color:var(--amber)">${d.label?.replace('\n', ' ')}</span>`;
    const cat = { CRITICAL: 'sb-crit', HIGH: 'sb-high', MEDIUM: 'sb-med', LOW: 'sb-low' }[d.category] || 'sb-ok';
    return `<div style="font-weight:600;color:var(--amber);margin-bottom:6px">${d.label}</div>
<div style="color:var(--anim-muted);font-size:10px;font-family:'Space Mono',monospace;margin-bottom:6px">${d.gstin}</div>
<span class="status-badge ${cat}">${d.category}</span>
<div style="margin-top:8px;display:grid;grid-template-columns:1fr 1fr;gap:4px;font-size:10px">
<span style="color:var(--anim-muted)">Risk:</span><span>${d.risk}/100</span>
<span style="color:var(--anim-muted)">ITC:</span><span>₹${(d.itc / 100000).toFixed(1)}L</span>
<span style="color:var(--anim-muted)">Filing:</span><span>${d.filingStreak}/24 mo</span>
<span style="color:var(--anim-muted)">Mismatches:</span><span style="color:${d.mismatches > 0 ? '#f97316' : '#22c55e'}">${d.mismatches}</span>
</div>`;
  }

  function ticked() {
    linkGRef.current?.selectAll('line')
      .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
    nodeGRef.current?.selectAll('g.node').attr('transform', d => `translate(${d.x},${d.y})`);
    labelGRef.current?.selectAll('.link-label')
      .attr('x', d => (d.source.x + d.target.x) / 2)
      .attr('y', d => (d.source.y + d.target.y) / 2 - 6);
  }

  function doReset(m) {
    animatingRef.current = false;
    animRunningRef.current = false;
    if (animIdRef.current) cancelAnimationFrame(animIdRef.current);
    animIdRef.current = null;
    particleDataRef.current = [];
    visitedRef.current.clear();
    blockedRef.current.clear();

    const mNodes = getNodesForMode(m);
    const mLinks = getLinksForMode(m);
    const canvas = svgRef.current?.closest('.trav-canvas');
    const cr = canvas?.getBoundingClientRect();
    const cW = cr?.width || window.innerWidth - 490;
    const cH = cr?.height || 520;

    simRef.current?.nodes(mNodes);
    simRef.current?.force('link').links(mLinks);
    simRef.current?.force('center', d3.forceCenter(cW / 2, cH / 2));
    simRef.current?.alpha(1).restart();

    drawLinks(mLinks);
    drawNodes(mNodes);
    buildStepBar(m);
    updateStepBar(-1);
    particleLayerRef.current?.selectAll('*').remove();
    resetNodeStyles();

    if (kpiEligibleRef.current) kpiEligibleRef.current.textContent = '--';
    if (kpiBlockedRef.current) kpiBlockedRef.current.textContent = '--';
    if (kpiHopsRef.current) kpiHopsRef.current.textContent = '0';
    if (kpiStatusRef.current) kpiStatusRef.current.textContent = 'IDLE';
    if (nodeInfoRef.current) nodeInfoRef.current.textContent = 'Hover over a node to inspect';
    if (stepLabelRef.current) stepLabelRef.current.textContent = 'Click Run Traversal to start';
    if (btnPlayRef.current) { btnPlayRef.current.disabled = false; btnPlayRef.current.textContent = '▶ Run Traversal'; }

    animRunningRef.current = true;
    animateParticles();
  }

  async function runITCAnimation() {
    const baseDelay = getSpeed() * 600;
    visitedRef.current.clear(); blockedRef.current.clear();
    visitedRef.current.add('n0');
    highlightNode('n0', '#6366f1', true);
    pulseNode('n0');
    addLog('Initiating ITC chain BFS from ACME Exports (Hop 0)', 'info');
    addLog('Section 16(2)(aa) CGST — tracing upstream supply chain', 'info');
    if (kpiHopsRef.current) kpiHopsRef.current.textContent = '0';
    if (kpiStatusRef.current) kpiStatusRef.current.textContent = 'TRAVERSING';
    updateStepBar(0);
    await sleep(baseDelay);

    updateStepBar(1);
    addLog('→ Hop 1: Checking direct suppliers n1, n2', 'hop');
    for (const id of ['n1', 'n2']) {
      const n = NODES.find(x => x.id === id);
      visitedRef.current.add(id);
      highlightLink('n0', id, '#f59e0b');
      startParticleStream([['n0', id]], '#f59e0b');
      await sleep(baseDelay / 2);
      highlightNode(id, n.status === 'BLOCKED' ? '#ef4444' : n.risk >= 60 ? '#f97316' : '#eab308');
      addLog(`  [HOP1] ${n.label} — Risk: ${n.risk} | Streak: ${n.filingStreak}mo | Mismatches: ${n.mismatches}`,
        n.risk >= 70 ? 'crit' : n.risk >= 50 ? 'warn' : 'ok');
      if (kpiHopsRef.current) kpiHopsRef.current.textContent = '1';
      await sleep(baseDelay / 2);
    }

    updateStepBar(2);
    for (const id of ['m1', 'm3']) {
      highlightLink('n1', 'm1', '#ef4444');
      highlightLink('n2', 'm3', '#ef4444');
      startParticleStream([['n1', 'm1'], ['n2', 'm3']], '#ef4444');
      d3.select('#node-' + id).select('rect').transition().duration(300).attr('fill', '#450a0a').attr('stroke-width', 2.5);
      await sleep(baseDelay / 3);
    }
    addLog('⚠ IRN_MISMATCH on INV-0042 at Mahindra Castings — ITC at risk', 'warn');
    addLog('⚠ AMOUNT_MISMATCH on INV-0078 at Flex Systems', 'warn');
    await sleep(baseDelay);

    updateStepBar(3);
    addLog('→ Hop 2: Checking second-tier suppliers n3, n4, n5', 'hop');
    for (const id of ['n3', 'n4', 'n5']) {
      const n = NODES.find(x => x.id === id);
      if (!n) continue;
      const parent = id === 'n3' || id === 'n4' ? 'n1' : 'n2';
      visitedRef.current.add(id);
      highlightLink(parent, id, id === 'n3' ? '#ef4444' : '#eab308');
      startParticleStream([[parent, id]], id === 'n3' ? '#ef4444' : '#eab308');
      await sleep(baseDelay / 2);
      highlightNode(id, id === 'n3' ? '#ef4444' : n.risk >= 60 ? '#f97316' : '#eab308');
      addLog(`  [HOP2] ${n.label} — Risk: ${n.risk} | ${id === 'n3' ? 'BLOCKED — Invoice missing in GSTR-2B' : 'Filing streak: ' + n.filingStreak + 'mo'}`,
        id === 'n3' ? 'crit' : n.risk >= 50 ? 'warn' : 'ok');
      if (kpiHopsRef.current) kpiHopsRef.current.textContent = '2';
      await sleep(baseDelay / 2);
    }

    updateStepBar(4);
    addLog('🚨 CRITICAL: Gujarat Agro (n3) — GSTR-1 NOT FILED for Oct 2024', 'crit');
    addLog('  → Invoice INV-0091 will NOT appear in ACME\'s GSTR-2B', 'crit');
    addLog('  → Section 16(2)(aa): ITC of ₹9.8L is INADMISSIBLE', 'crit');
    highlightNode('n3', '#ef4444', true);
    d3.select('#node-n3').select('circle.node-circle').attr('stroke', '#ef4444').attr('stroke-width', 4).attr('filter', 'url(#glow)');
    flashNode('n3', '#ef4444');
    blockedRef.current.add('n3');
    if (kpiBlockedRef.current) kpiBlockedRef.current.textContent = '₹9.8L';
    await sleep(baseDelay * 1.2);

    updateStepBar(5);
    addLog('→ Hop 3: Checking third-tier suppliers n6, n7', 'hop');
    for (const id of ['n6', 'n7']) {
      const n = NODES.find(x => x.id === id);
      if (!n) continue;
      const parent = id === 'n6' ? 'n3' : 'n4';
      visitedRef.current.add(id);
      const col = id === 'n6' ? '#ef4444' : '#eab308';
      highlightLink(parent, id, col);
      startParticleStream([[parent, id]], col);
      await sleep(baseDelay / 2);
      highlightNode(id, n.risk >= 50 ? '#f97316' : '#eab308');
      addLog(`  [HOP3] ${n.label} — Risk: ${n.risk}`, n.risk >= 50 ? 'warn' : 'ok');
      if (kpiHopsRef.current) kpiHopsRef.current.textContent = '3';
      await sleep(baseDelay / 2);
    }

    updateStepBar(6);
    dimUnvisited();
    if (kpiEligibleRef.current) kpiEligibleRef.current.textContent = '₹70.2L';
    if (kpiBlockedRef.current) kpiBlockedRef.current.textContent = '₹9.8L';
    if (kpiStatusRef.current) kpiStatusRef.current.textContent = 'COMPLETE';
    addLog('═══════════════════════════════════', 'info');
    addLog('BFS COMPLETE — Chain Risk Level: HIGH', 'crit');
    addLog('Total ITC Eligible: ₹80.2L', 'ok');
    addLog('Total ITC Blocked: ₹9.8L (at Hop 2 — Gujarat Agro)', 'crit');
    addLog('Blocked by: Section 16(2)(aa) — Invoice not in GSTR-2B', 'crit');
    addLog('Action: Reverse ₹9.8L ITC in next GSTR-3B filing', 'warn');
    if (kpiHopsRef.current) kpiHopsRef.current.textContent = '3';

    setInterval(() => { if (animRunningRef.current) startParticleStream([['n0', 'n1'], ['n0', 'n2'], ['n1', 'n4'], ['n2', 'n5'], ['n4', 'n7']], '#f59e0b'); }, 1200);
  }

  async function runFraudAnimation() {
    const baseDelay = getSpeed() * 700;
    if (kpiStatusRef.current) kpiStatusRef.current.textContent = 'SCANNING';
    addLog('Initiating circular trading scan — fraud detection mode', 'info');
    addLog('Algorithm: DFS with cycle detection (Karp\'s algorithm)', 'info');
    await sleep(baseDelay);

    updateStepBar(0);
    highlightNode('n1', '#a855f7', true);
    addLog('→ Starting DFS from Mahindra Castings', 'hop');
    await sleep(baseDelay);

    updateStepBar(1);
    highlightLink('n1', 'n2', '#a855f7');
    startParticleStream([['n1', 'n2']], '#a855f7');
    await sleep(baseDelay / 2);
    highlightNode('n2', '#a855f7');
    addLog('→ n1 → n2 (Flex Systems) — ₹2.2L transaction', 'hop');
    await sleep(baseDelay);

    updateStepBar(2);
    highlightLink('n2', 'n3', '#a855f7');
    startParticleStream([['n2', 'n3']], '#a855f7');
    await sleep(baseDelay / 2);
    highlightNode('n3', '#a855f7');
    addLog('→ n2 → n3 (Gujarat Agro) — ₹2.1L transaction', 'hop');
    await sleep(baseDelay);

    updateStepBar(3);
    highlightLink('n3', 'n1', '#ef4444');
    startParticleStream([['n3', 'n1']], '#ef4444');
    await sleep(baseDelay / 2);
    addLog('🚨🚨 CYCLE DETECTED: n3 → n1 closes the ring!', 'crit');
    addLog('   Mahindra → Flex Systems → Gujarat Agro → Mahindra', 'crit');
    addLog('   Ring ITC value: ₹6.45 Lakh (synthetic/fake ITC)', 'crit');

    for (let i = 0; i < 4; i++) {
      await sleep(200);
      ['n1', 'n2', 'n3'].forEach(id => {
        d3.select('#node-' + id).select('circle.node-circle')
          .attr('stroke', '#ef4444').attr('stroke-width', 4).attr('fill', '#ef4444').attr('fill-opacity', .4);
      });
      await sleep(200);
      ['n1', 'n2', 'n3'].forEach(id => {
        const n = NODES.find(x => x.id === id);
        d3.select('#node-' + id).select('circle.node-circle')
          .attr('stroke', '#a855f7').attr('stroke-width', 3).attr('fill', nodeColor(n)).attr('fill-opacity', .2);
      });
    }

    updateStepBar(4);
    addLog('═══════════════════════════════════', 'info');
    addLog('FRAUD REPORT: 1 circular trading ring found', 'crit');
    addLog('Legal exposure: Section 132 CGST Act — Prosecution', 'crit');
    addLog('ITC to be reversed: ₹6.45L | Penalty: ₹6.45L (100%)', 'crit');
    if (kpiBlockedRef.current) kpiBlockedRef.current.textContent = '₹6.45L';
    if (kpiStatusRef.current) kpiStatusRef.current.textContent = 'FRAUD FOUND';

    setInterval(() => { if (animRunningRef.current) startParticleStream([['n1', 'n2'], ['n2', 'n3'], ['n3', 'n1']], '#a855f7'); }, 1000);
  }

  async function runGSTRAnimation() {
    const baseDelay = getSpeed() * 700;
    if (kpiStatusRef.current) kpiStatusRef.current.textContent = 'FILING';
    addLog('Simulating GSTR filing sequence for Oct 2024', 'info');
    addLog('Due dates: GSTR-1 (11-Nov), GSTR-2B (14-Nov), GSTR-3B (20-Nov)', 'info');
    await sleep(baseDelay);

    updateStepBar(0);
    highlightNode('n1', '#22c55e');
    addLog('✓ Mahindra Castings filed GSTR-1 on 11-Nov-2024', 'ok');
    highlightLink('n1', 'g1r1', '#22c55e');
    startParticleStream([['n1', 'g1r1']], '#22c55e');
    d3.select('#node-g1r1').select('rect').transition().duration(600).attr('fill', '#052e16').attr('stroke', '#22c55e').attr('stroke-width', 2.5);
    await sleep(baseDelay);

    updateStepBar(1);
    addLog('→ GSTN auto-generates GSTR-2B for ACME Exports on 14-Nov', 'info');
    highlightNode('n0', '#3b82f6');
    highlightLink('n0', 'g1r2', '#3b82f6');
    startParticleStream([['g1r1', 'g1r2']], '#3b82f6');
    d3.select('#node-g1r2').select('rect').transition().duration(600).attr('fill', '#0c1d3e').attr('stroke', '#3b82f6').attr('stroke-width', 2.5);
    await sleep(baseDelay);

    updateStepBar(2);
    addLog('🚨 Gujarat Agro FAILED to file GSTR-1 by 11-Nov deadline!', 'crit');
    addLog('   → Invoice INV-0091 (₹9.8L) will NOT appear in ACME\'s GSTR-2B', 'crit');
    highlightNode('n3', '#ef4444', true);
    d3.select('#node-g2r1').select('rect').transition().duration(600).attr('fill', '#450a0a').attr('stroke', '#ef4444').attr('stroke-width', 2.5);
    for (let i = 0; i < 3; i++) {
      await sleep(300);
      d3.select('#node-g2r1').attr('opacity', .3);
      await sleep(300);
      d3.select('#node-g2r1').attr('opacity', 1);
    }
    await sleep(baseDelay / 2);

    updateStepBar(3);
    addLog('→ ACME files GSTR-3B on 20-Nov claiming ITC from GSTR-2B', 'info');
    addLog('   ITC from Gujarat Agro\'s invoice — INADMISSIBLE', 'crit');
    addLog('   Exposure: ₹9.8L must be reversed + interest @18% p.a.', 'warn');
    highlightLink('n0', 'g3b', '#eab308');
    startParticleStream([['n0', 'g3b']], '#eab308');
    d3.select('#node-g3b').select('rect').transition().duration(600).attr('fill', '#1a0f00').attr('stroke', '#eab308');

    addLog('═══════════════════════════════════', 'info');
    addLog('GSTR FILING SEQUENCE COMPLETE', 'ok');
    addLog('Issue: 1 supplier non-filing creates downstream ITC risk', 'crit');
    if (kpiBlockedRef.current) kpiBlockedRef.current.textContent = '₹9.8L';
    if (kpiStatusRef.current) kpiStatusRef.current.textContent = 'COMPLETE';
  }

  async function animStart() {
    if (animatingRef.current) return;
    animatingRef.current = true;
    animRunningRef.current = true;
    if (btnPlayRef.current) { btnPlayRef.current.disabled = true; btnPlayRef.current.textContent = '⏳ Running...'; }

    simRef.current?.alpha(.1).restart();
    await sleep(800);
    animateParticles();

    const m = modeRef.current;
    if (m === 'itc') await runITCAnimation();
    else if (m === 'fraud') await runFraudAnimation();
    else await runGSTRAnimation();

    animatingRef.current = false;
    if (btnPlayRef.current) { btnPlayRef.current.disabled = false; btnPlayRef.current.textContent = '▶ Run Again'; }
  }

  function handleModeChange(m) {
    modeRef.current = m;
    setMode(m);
    doReset(m);
  }

  useEffect(() => {
    if (inited.current) return;
    inited.current = true;

    const svgEl = svgRef.current;
    const canvasEl = svgEl?.closest('.trav-canvas');
    const rect = canvasEl?.getBoundingClientRect();
    const W = rect?.width || window.innerWidth - 500;
    const H = rect?.height || 520;

    const svgSel = d3.select(svgEl)
      .call(d3.zoom().scaleExtent([.4, 3]).on('zoom', e => container.attr('transform', e.transform)));
    svgSelRef.current = svgSel;
    const container = svgSel.append('g').attr('id', 'container');

    const defs = svgSel.append('defs');
    const mkArrow = (id, color) => defs.append('marker').attr('id', id)
      .attr('viewBox', '0 0 10 10').attr('refX', 28).attr('refY', 5)
      .attr('markerWidth', 5).attr('markerHeight', 5).attr('orient', 'auto')
      .append('path').attr('d', 'M 0 0 L 10 5 L 0 10 z').attr('fill', color).attr('opacity', .8);
    mkArrow('arr-default', '#334155');
    mkArrow('arr-active', '#f59e0b');
    mkArrow('arr-blocked', '#ef4444');
    mkArrow('arr-ok', '#22c55e');
    mkArrow('arr-circular', '#a855f7');
    mkArrow('arr-gstr', '#3b82f6');

    const blur = defs.append('filter').attr('id', 'glow').attr('x', '-30%').attr('y', '-30%').attr('width', '160%').attr('height', '160%');
    blur.append('feGaussianBlur').attr('stdDeviation', '4').attr('result', 'blur');
    const feMerge = blur.append('feMerge');
    feMerge.append('feMergeNode').attr('in', 'blur');
    feMerge.append('feMergeNode').attr('in', 'SourceGraphic');

    particleLayerRef.current = container.append('g').attr('id', 'particles');
    linkGRef.current = container.append('g').attr('id', 'links');
    nodeGRef.current = container.append('g').attr('id', 'nodes');
    labelGRef.current = container.append('g').attr('id', 'labels');

    const modeLinks = getLinksForMode('itc');
    const modeNodes = getNodesForMode('itc');

    simRef.current = d3.forceSimulation(modeNodes)
      .force('link', d3.forceLink(modeLinks).id(d => d.id).distance(d => d.type === 'HAS_MISMATCH' ? 80 : d.type === 'FILED' ? 90 : 120).strength(.7))
      .force('charge', d3.forceManyBody().strength(-350))
      .force('center', d3.forceCenter(W / 2, H / 2))
      .force('collision', d3.forceCollide(50))
      .on('tick', ticked);

    doReset('itc');

    const idleInterval = setInterval(() => {
      if (!animatingRef.current && animRunningRef.current) {
        const pairs = [['n0', 'n1'], ['n1', 'n3'], ['n0', 'n2']];
        const pair = pairs[Math.floor(Math.random() * pairs.length)];
        spawnParticles(pair[0], pair[1], '#334155', 1);
      }
    }, 800);

    return () => {
      clearInterval(idleInterval);
      animRunningRef.current = false;
      if (animIdRef.current) cancelAnimationFrame(animIdRef.current);
      simRef.current?.stop();
    };
  }, []);

  return (
    <div className="traversal-page">
      <div className="traversal-wrap">
        <div className="trav-controls">
          <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--amber)', marginRight: '6px' }}>⚡ Live Graph Traversal</span>
          {['itc', 'fraud', 'gstr'].map(m => (
            <button key={m} className={`trav-mode-btn${mode === m ? ' active' : ''}`} onClick={() => handleModeChange(m)}>
              {m === 'itc' ? 'ITC Chain' : m === 'fraud' ? 'Fraud Ring' : 'GSTR Filing'}
            </button>
          ))}
          <div style={{ flex: 1 }} />
          <span className="trav-speed-label">Speed</span>
          <input className="trav-speed-range" type="range" min="1" max="5" defaultValue="3" ref={speedRangeRef} />
          <button className="btn btn-amber" ref={btnPlayRef} onClick={animStart}>▶ Run Traversal</button>
          <button className="btn btn-outline" style={{ borderColor: '#1e2d4a', color: '#e2e8f0', background: 'transparent' }} onClick={() => doReset(modeRef.current)}>↺ Reset</button>
        </div>

        <div className="trav-kpi-strip">
          <div className="trav-kpi-item"><div className="trav-kpi-lbl">ITC Eligible</div><div className="trav-kpi-val" ref={kpiEligibleRef} style={{ color: 'var(--low)' }}>--</div></div>
          <div className="trav-kpi-item"><div className="trav-kpi-lbl">ITC Blocked</div><div className="trav-kpi-val" ref={kpiBlockedRef} style={{ color: 'var(--critical)' }}>--</div></div>
          <div className="trav-kpi-item"><div className="trav-kpi-lbl">Hops Traversed</div><div className="trav-kpi-val" ref={kpiHopsRef} style={{ color: 'var(--amber)' }}>0</div></div>
          <div className="trav-kpi-item"><div className="trav-kpi-lbl">Status</div><div className="trav-kpi-val" ref={kpiStatusRef} style={{ fontSize: '11px', color: 'var(--anim-muted)' }}>IDLE</div></div>
        </div>

        <div className="trav-body">
          <div className="trav-sidebar">
            <div className="trav-sb-section">
              <div className="trav-sb-title">Traversal Mode</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                {['itc', 'fraud', 'gstr'].map(m => (
                  <div key={m} className={`trav-mode-btn${mode === m ? ' active' : ''}`} style={{ textAlign: 'center', cursor: 'pointer' }} onClick={() => handleModeChange(m)}>
                    {m === 'itc' ? 'ITC Chain BFS' : m === 'fraud' ? 'Circular Fraud' : 'GSTR Filing'}
                  </div>
                ))}
              </div>
            </div>
            <div className="trav-sb-section">
              <div className="trav-sb-title">Traversal Progress</div>
              <div className="trav-step-bar">
                {stepDots.map((s, i) => (
                  <div key={i} className={`trav-step-dot${s === 'done' ? ' done' : s === 'active' ? ' active' : ''}`} />
                ))}
              </div>
              <div style={{ marginTop: '6px', fontSize: '10px', color: 'var(--anim-muted)' }} ref={stepLabelRef}>Click Run Traversal to start</div>
            </div>
            <div className="trav-sb-section">
              <div className="trav-sb-title">Node Legend</div>
              <div className="trav-legend-row"><div className="trav-legend-dot" style={{ background: 'var(--hop0)' }} />Recipient (Hop 0)</div>
              <div className="trav-legend-row"><div className="trav-legend-dot" style={{ background: 'var(--low)' }} />Safe — Compliant Vendor</div>
              <div className="trav-legend-row"><div className="trav-legend-dot" style={{ background: 'var(--medium)' }} />Warning — Mismatches</div>
              <div className="trav-legend-row"><div className="trav-legend-dot" style={{ background: 'var(--critical)' }} />Blocked — ITC Invalid</div>
              <div className="trav-legend-row"><div className="trav-legend-dot" style={{ background: 'var(--anim-muted)' }} />Unvisited Node</div>
              <div className="trav-legend-row"><div className="trav-legend-rect" style={{ background: 'var(--critical)' }} />Mismatch Event</div>
              <div style={{ marginTop: '6px', fontSize: '10px', color: 'var(--anim-muted)' }}>Edge particles = tax / transaction flow</div>
            </div>
            <div className="trav-sb-section">
              <div className="trav-sb-title">Active Node Info</div>
              <div ref={nodeInfoRef} style={{ fontSize: '11px', color: 'var(--anim-muted)' }}>Hover over a node to inspect</div>
            </div>
            <div className="trav-sb-section" style={{ flex: 0 }}>
              <div className="trav-sb-title">Traversal Log</div>
            </div>
            <div className="trav-log-area">
              {logEntries.map((entry, i) => (
                <div key={i} className="trav-log-entry">
                  <span className="trav-log-ts">{entry.ts}</span>
                  <span className={`${entry.cls} trav-log-msg`}>{entry.msg}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="trav-canvas">
            <svg ref={svgRef} id="graph-svg" />
            <div className="anim-tooltip" ref={tooltipRef} />
          </div>
        </div>
      </div>
    </div>
  );
}
