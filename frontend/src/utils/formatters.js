export const inr = v => '₹' + new Intl.NumberFormat('en-IN').format(Math.round(v));

export const riskColor = r => ({CRITICAL:'#ef4444',HIGH:'#f97316',MEDIUM:'#eab308',LOW:'#22c55e'}[r]||'#94a3b8');

export const riskBadge = r => `badge badge-${r.toLowerCase()}`;

export const statusBadge = s => `badge ${s==='RESOLVED'?'badge-resolved':s==='IN_PROGRESS'?'badge-progress':'badge-pending'}`;

export const mismatchIcon = t => ({IRN_MISMATCH:'⚠️',AMOUNT_MISMATCH:'💰',INVOICE_MISSING_2B:'📭',EXTRA_IN_2B:'📬',GSTIN_MISMATCH:'🆔',DATE_MISMATCH:'📅',EWAYBILL_MISSING:'🚚',PAYMENT_OVERDUE_180_DAYS:'⏱'}[t]||'❓');
