"""
Deliverable 2B — GST Knowledge Graph Reconciliation Engine
===========================================================
Uses NetworkX DiGraph to model India's GST ecosystem and perform:

  1. Multi-hop ITC chain validation (BFS traversal)
  2. Period-level reconciliation (GSTR-1 vs GSTR-2B matching)
  3. Risk cluster detection (connected components analysis)
  4. Graph statistics

Why NetworkX?
  - Native graph traversal without SQL JOINs
  - Built-in BFS/DFS with cycle detection
  - Connected components for cluster analysis
  - Works without external database (demo-ready)

Production path:
  Replace NetworkX with Neo4j py2neo/driver
  Same traversal logic, just different query language (Cypher)
  NetworkX algorithms → Neo4j GDS library
"""

import json
import networkx as nx
from pathlib import Path
from collections import defaultdict, deque
from datetime import date, datetime, timedelta
from typing import Optional

from schema import MISMATCH_TAXONOMY

DATA_DIR = Path(__file__).parent / "data"

RISK_ORDER = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}


class GSTKnowledgeGraph:
    """
    NetworkX-based GST Knowledge Graph.

    Graph structure:
      Nodes: taxpayer_*, gstin_*, invoice_*, irn_*, return_*,
             mismatch_*, ewb_*, payment_*
      Edges: typed relationships per schema.py EDGE_SCHEMA

    Scalability note:
      This in-memory implementation handles thousands of nodes.
      Production: Neo4j handles billions of nodes with native
      graph algorithms (PageRank, Louvain, GDS library).
    """

    def __init__(self):
        self.G: nx.DiGraph         = nx.DiGraph()
        self.taxpayers:  list      = []
        self.invoices:   list      = []
        self.mismatches: list      = []
        self.vendors:    list      = []
        self.returns:    list      = []
        self.payments:   list      = []

        # Lookup indexes (for O(1) access)
        self._gstin_to_tp:   dict  = {}  # gstin → taxpayer dict
        self._inv_index:     dict  = {}  # invoice_id → invoice dict
        self._mis_index:     dict  = {}  # mismatch_id → mismatch dict
        self._inv_by_buyer:  dict  = defaultdict(list)  # (buyer_gstin, period) → invoices
        self._inv_by_sup:    dict  = defaultdict(list)  # (supplier_gstin, period) → invoices
        self._mis_by_inv:    dict  = defaultdict(list)  # invoice_id → mismatches
        self._pay_by_inv:    dict  = {}  # invoice_id → payment dict (single payment per invoice)

    # ──────────────────────────────────────────────────────────
    # DATA LOADING
    # ──────────────────────────────────────────────────────────

    def load_data(self):
        """
        Load all JSON files from /data directory.
        Triggers graph construction.
        """
        files = {
            "taxpayers":  "taxpayers.json",
            "invoices":   "invoices.json",
            "mismatches": "mismatches.json",
            "vendors":    "vendors.json",
            "returns":    "returns.json",
            "payments":   "payments.json",
        }
        for attr, fname in files.items():
            path = DATA_DIR / fname
            if path.exists():
                with open(path, encoding="utf-8") as f:
                    setattr(self, attr, json.load(f))
            else:
                print(f"  [WARN]  {fname} not found — run data_generator.py first")

        self._build_indexes()
        self._build_graph()
        print(f"[OK] Graph loaded: {self.G.number_of_nodes()} nodes, "
              f"{self.G.number_of_edges()} edges")

    def _build_indexes(self):
        """Build O(1) lookup indexes from loaded data."""
        for tp in self.taxpayers:
            self._gstin_to_tp[tp["gstin"]] = tp

        for inv in self.invoices:
            self._inv_index[inv["invoice_id"]] = inv
            self._inv_by_buyer[(inv["buyer_gstin"], inv["return_period"])].append(inv)
            self._inv_by_sup[(inv["supplier_gstin"], inv["return_period"])].append(inv)

        for m in self.mismatches:
            self._mis_index[m["mismatch_id"]] = m
            self._mis_by_inv[m["invoice_id"]].append(m)

        for pay in self.payments:
            self._pay_by_inv[pay["invoice_id"]] = pay

    def _build_graph(self):
        """
        Construct NetworkX DiGraph from loaded data.
        Node types identified by 'type' attribute.
        Edge types identified by 'type' attribute.

        Node ID conventions:
          Taxpayer:      tp_{taxpayer_id}
          GSTIN:         gstin_{gstin}
          Invoice:       inv_{invoice_id}
          Return:        ret_{return_id}
          MismatchEvent: mis_{mismatch_id}
        """
        # ── Taxpayer + GSTIN nodes ─────────────────────────
        for tp in self.taxpayers:
            tp_id = f"tp_{tp['taxpayer_id']}"
            self.G.add_node(tp_id, type="Taxpayer", **tp)

            g_id = f"gstin_{tp['gstin']}"
            self.G.add_node(g_id, type="GSTIN",
                gstin=tp["gstin"], state_code=tp["state_code"],
                status=tp["status"], registration_type=tp["category"],
                annual_turnover=tp["annual_turnover"],
                filing_frequency=tp["filing_frequency"],
                compliance_score=tp["compliance_score"],
                name=tp["name"],
            )
            # REGISTERED_AS edge
            self.G.add_edge(tp_id, g_id, type="REGISTERED_AS")

        # ── Invoice + IRN nodes ────────────────────────────
        for inv in self.invoices:
            inv_id = f"inv_{inv['invoice_id']}"
            self.G.add_node(inv_id, type="Invoice", **inv)

            sup_g  = f"gstin_{inv['supplier_gstin']}"
            buy_g  = f"gstin_{inv['buyer_gstin']}"

            # SUPPLIER_OF edge
            if self.G.has_node(sup_g):
                self.G.add_edge(sup_g, inv_id, type="SUPPLIER_OF",
                                supply_type=inv["supply_type"])

            # RECIPIENT_OF edge
            if self.G.has_node(buy_g):
                self.G.add_edge(inv_id, buy_g, type="RECIPIENT_OF",
                                itc_eligible=inv.get("irn_status") == "ACTIVE" or
                                             inv["taxable_value"] < 500_000)

            # TRANSACTS_WITH edge (GSTIN → GSTIN)
            if self.G.has_node(sup_g) and self.G.has_node(buy_g):
                if self.G.has_edge(sup_g, buy_g):
                    self.G[sup_g][buy_g]["transaction_count"] = \
                        self.G[sup_g][buy_g].get("transaction_count", 0) + 1
                    self.G[sup_g][buy_g]["total_value"] = \
                        self.G[sup_g][buy_g].get("total_value", 0) + inv["total_value"]
                else:
                    self.G.add_edge(sup_g, buy_g, type="TRANSACTS_WITH",
                                    transaction_count=1,
                                    total_value=inv["total_value"],
                                    risk_flag=False)

            # IRN node (only for invoices with IRN)
            if inv.get("irn"):
                irn_id = f"irn_{inv['invoice_id']}"
                self.G.add_node(irn_id, type="IRN",
                    irn=inv["irn"], status=inv.get("irn_status", "ACTIVE"),
                    ack_no=f"ACK{hash(inv['irn']) % 10**15:015d}",
                    ack_date=inv["invoice_date"],
                )
                self.G.add_edge(inv_id, irn_id, type="HAS_IRN")

        # ── Return nodes ───────────────────────────────────
        for ret in self.returns:
            ret_id = f"ret_{ret['return_id']}"
            self.G.add_node(ret_id, type="Return", **ret)
            g_id = f"gstin_{ret['gstin']}"
            if self.G.has_node(g_id):
                self.G.add_edge(g_id, ret_id, type="FILED_RETURN")

        # ── MismatchEvent nodes ────────────────────────────
        for m in self.mismatches:
            mis_id = f"mis_{m['mismatch_id']}"
            self.G.add_node(mis_id, type="MismatchEvent", **m)
            inv_id = f"inv_{m['invoice_id']}"
            if self.G.has_node(inv_id):
                self.G.add_edge(inv_id, mis_id, type="HAS_MISMATCH")

            # Flag TRANSACTS_WITH edge as risky if critical mismatch
            if m["risk_level"] == "CRITICAL":
                sup_g = f"gstin_{m['supplier_gstin']}"
                inv   = self._inv_index.get(m["invoice_id"], {})
                if inv:
                    buy_g = f"gstin_{inv.get('buyer_gstin', '')}"
                    if self.G.has_edge(sup_g, buy_g):
                        self.G[sup_g][buy_g]["risk_flag"] = True

        # ── SupplierPayment nodes ──────────────────────────
        # Models Section 16(2)(b): buyer-to-supplier payment tracking.
        # Absence of a PAID_BY edge after 180 days = ITC reversal required.
        today = date.today()
        for pay in self.payments:
            pay_id = f"pay_{pay['payment_id']}"
            self.G.add_node(pay_id, type="SupplierPayment", **pay)
            inv_id = f"inv_{pay['invoice_id']}"
            if self.G.has_node(inv_id):
                self.G.add_edge(
                    inv_id, pay_id,
                    type="PAID_BY",
                    days_from_invoice=pay["days_from_invoice"],
                    is_overdue=pay["is_overdue"],
                )

    # ──────────────────────────────────────────────────────────
    # RECONCILIATION ENGINE
    # ──────────────────────────────────────────────────────────

    def reconcile_period(self, gstin: str, period: str) -> dict:
        """
        Reconcile Purchase Register (all invoices for this buyer in period)
        vs GSTR-2B (invoices confirmed by supplier GSTR-1).

        Logic:
          Purchase Register = all invoices where buyer_gstin == gstin
          GSTR-2B eligible  = invoices where supplier filed GSTR-1 AND no INVOICE_MISSING_2B mismatch
          Matched           = in both Purchase Register AND GSTR-2B
          Mismatched        = in Purchase Register but NOT in GSTR-2B (or has mismatch)

        Returns:
          match_rate, total_itc_at_risk, classified_mismatches
        """
        pr_invoices = self._inv_by_buyer.get((gstin, period), [])
        if not pr_invoices:
            return {
                "gstin": gstin, "period": period,
                "status": "NO_INVOICES",
                "match_rate": 0.0, "total_itc_at_risk": 0.0,
                "matched_count": 0, "total_count": 0,
                "classified_mismatches": [],
            }

        classified   = []
        total_itc    = 0.0
        matched_itc  = 0.0
        matched_count= 0
        today        = date.today()

        for inv in pr_invoices:
            inv_mismatches = self._mis_by_inv.get(inv["invoice_id"], [])
            has_2b_miss    = any(m["mismatch_type"] == "INVOICE_MISSING_2B" for m in inv_mismatches)
            has_mismatch   = len(inv_mismatches) > 0
            itc_value      = inv["igst"] + inv["cgst"] + inv["sgst"]
            total_itc     += itc_value

            # ── Section 16(2)(b): 180-day payment check ──────────────────
            inv_date  = datetime.strptime(inv["invoice_date"], "%Y-%m-%d").date()
            days_old  = (today - inv_date).days
            payment   = self._pay_by_inv.get(inv["invoice_id"])

            payment_status = "PAID"
            payment_days   = None
            itc_reversal_due = False

            if payment is None:
                # No payment at all
                payment_status   = "UNPAID"
                payment_days     = days_old
                if days_old > 180:
                    itc_reversal_due = True
            elif payment["is_overdue"]:
                # Paid but after 180 days — ITC was reversed, now re-claimable
                payment_status   = "PAID_AFTER_180_DAYS"
                payment_days     = payment["days_from_invoice"]
            else:
                payment_days = payment["days_from_invoice"]

            # Inject PAYMENT_OVERDUE_180_DAYS as a synthetic mismatch if triggered
            if itc_reversal_due and not any(
                m["mismatch_type"] == "PAYMENT_OVERDUE_180_DAYS" for m in inv_mismatches
            ):
                interest = round(itc_value * 0.18 * (days_old / 365), 2)
                synthetic_mis = {
                    "mismatch_id":   f"SYN-PAY-{inv['invoice_id']}",
                    "mismatch_type": "PAYMENT_OVERDUE_180_DAYS",
                    "invoice_id":    inv["invoice_id"],
                    "invoice_no":    inv["invoice_no"],
                    "supplier_gstin":inv["supplier_gstin"],
                    "buyer_gstin":   inv["buyer_gstin"],
                    "return_period": inv["return_period"],
                    "detected_date": today.strftime("%Y-%m-%d"),
                    "gstr1_value":   inv["taxable_value"],
                    "gstr2b_value":  inv["taxable_value"],
                    "amount_at_risk":itc_value,
                    "interest_liability": interest,
                    "days_overdue":  days_old,
                    "risk_level":    "CRITICAL",
                    "root_cause":    f"Invoice unpaid for {days_old} days (threshold: 180). ITC reversal + ₹{interest:,.0f} interest liability.",
                    "resolution_status": "PENDING",
                }
                inv_mismatches = list(inv_mismatches) + [synthetic_mis]
                has_mismatch   = True
            # ── end 180-day check ─────────────────────────────────────────

            if not has_mismatch:
                matched_count += 1
                matched_itc   += itc_value
                status         = "MATCHED"
                risk_level     = "LOW"
                at_risk        = 0.0
            elif has_2b_miss:
                status    = "MISSING_IN_2B"
                risk_level= "HIGH"
                at_risk   = itc_value
            else:
                # Pick highest risk mismatch
                top_mis    = max(inv_mismatches, key=lambda m: RISK_ORDER.get(m["risk_level"], 0))
                status     = top_mis["mismatch_type"]
                risk_level = top_mis["risk_level"]
                at_risk    = sum(m["amount_at_risk"] for m in inv_mismatches)

            classified.append({
                "invoice_id":    inv["invoice_id"],
                "invoice_no":    inv["invoice_no"],
                "supplier_gstin":inv["supplier_gstin"],
                "supplier_name": inv["supplier_name"],
                "taxable_value": inv["taxable_value"],
                "itc_value":     round(itc_value, 2),
                "status":        status,
                "risk_level":    risk_level,
                "at_risk":       round(at_risk, 2),
                "mismatches":    inv_mismatches,
                # Payment tracking fields (Section 16(2)(b))
                "payment_status":  payment_status,
                "payment_days":    payment_days,
                "itc_reversal_due":itc_reversal_due,
            })

        total_at_risk = sum(c["at_risk"] for c in classified)
        match_rate    = round(matched_count / len(pr_invoices) * 100, 1) if pr_invoices else 0.0

        classified.sort(key=lambda x: RISK_ORDER.get(x["risk_level"], 0), reverse=True)

        return {
            "gstin":               gstin,
            "period":              period,
            "total_count":         len(pr_invoices),
            "matched_count":       matched_count,
            "mismatched_count":    len(pr_invoices) - matched_count,
            "match_rate":          match_rate,
            "total_itc_pool":      round(total_itc, 2),
            "total_itc_at_risk":   round(total_at_risk, 2),
            "classified_mismatches": classified,
        }

    def check_payment_compliance(self, gstin: str, as_of_date: Optional[str] = None) -> dict:
        """
        Section 16(2)(b) CGST Act — 180-Day Payment Compliance Check.

        Scans ALL invoices where this GSTIN is the BUYER and checks:
          1. UNPAID invoices older than 180 days → ITC must be reversed NOW
          2. PAID AFTER 180 DAYS → ITC was to be reversed; re-claimable now
          3. PAID WITHIN 180 DAYS → Safe, no action needed
          4. PENDING (< 180 days, unpaid) → Countdown warning

        Returns:
          - overdue_list: invoices requiring immediate ITC reversal
          - paid_late_list: paid after 180 days (ITC was reversed; now re-claimable)
          - pending_list: approaching the 180-day threshold (warning)
          - total_reversal_required: sum of ITC to reverse today
          - total_interest: 18% p.a. interest on overdue amounts
        """
        check_date = (
            datetime.strptime(as_of_date, "%Y-%m-%d").date()
            if as_of_date
            else date.today()
        )

        overdue_list  = []
        paid_late_list= []
        pending_list  = []
        safe_count    = 0

        # Get all invoices where this GSTIN is the BUYER
        buyer_invoices = [
            inv for inv in self.invoices
            if inv["buyer_gstin"] == gstin
        ]

        for inv in buyer_invoices:
            itc_value = inv["igst"] + inv["cgst"] + inv["sgst"]
            if itc_value == 0:
                continue  # No ITC on zero-tax invoices

            inv_date  = datetime.strptime(inv["invoice_date"], "%Y-%m-%d").date()
            days_old  = (check_date - inv_date).days
            payment   = self._pay_by_inv.get(inv["invoice_id"])

            base_info = {
                "invoice_id":    inv["invoice_id"],
                "invoice_no":    inv["invoice_no"],
                "invoice_date":  inv["invoice_date"],
                "supplier_gstin":inv["supplier_gstin"],
                "supplier_name": inv["supplier_name"],
                "taxable_value": inv["taxable_value"],
                "itc_value":     round(itc_value, 2),
                "days_old":      days_old,
            }

            if payment is None:
                if days_old > 180:
                    # CRITICAL: ITC must be reversed
                    interest = round(itc_value * 0.18 * (days_old / 365), 2)
                    overdue_list.append({
                        **base_info,
                        "status":             "UNPAID_OVERDUE",
                        "days_overdue":       days_old - 180,
                        "itc_to_reverse":     round(itc_value, 2),
                        "interest_liability": interest,
                        "total_liability":    round(itc_value + interest, 2),
                        "legal_ref":          "Section 16(2)(b) CGST Act",
                        "action":             "Reverse ITC in GSTR-3B Table 4(B)(2) immediately",
                    })
                elif days_old > 150:
                    # WARNING: Approaching 180-day threshold
                    days_left = 180 - days_old
                    pending_list.append({
                        **base_info,
                        "status":      "PAYMENT_PENDING_WARNING",
                        "days_left":   days_left,
                        "itc_at_risk": round(itc_value, 2),
                        "action":      f"Pay supplier within {days_left} days to retain ITC",
                    })
                else:
                    safe_count += 1
            elif payment["is_overdue"]:
                # Paid after 180 days — ITC was reversed, now re-claimable
                pay_date    = datetime.strptime(payment["payment_date"], "%Y-%m-%d").date()
                reversal_days = payment["days_from_invoice"] - 180
                interest    = round(itc_value * 0.18 * (reversal_days / 365), 2)
                paid_late_list.append({
                    **base_info,
                    "status":             "PAID_AFTER_180_DAYS",
                    "payment_date":       payment["payment_date"],
                    "days_from_invoice":  payment["days_from_invoice"],
                    "reversal_period_days": reversal_days,
                    "interest_paid":      interest,
                    "itc_re_claimable":   round(itc_value, 2),
                    "action":             f"Re-claim ITC in GSTR-3B for period {pay_date.strftime('%m%Y')}",
                })
            else:
                safe_count += 1

        total_reversal = sum(i["itc_to_reverse"] for i in overdue_list)
        total_interest = sum(i["interest_liability"] for i in overdue_list)
        total_reclaim  = sum(i["itc_re_claimable"] for i in paid_late_list)

        return {
            "gstin":                 gstin,
            "as_of_date":            check_date.strftime("%Y-%m-%d"),
            "total_invoices_checked":len(buyer_invoices),
            "safe_count":            safe_count,
            "overdue_count":         len(overdue_list),
            "paid_late_count":       len(paid_late_list),
            "pending_warning_count": len(pending_list),
            "total_itc_reversal_required": round(total_reversal, 2),
            "total_interest_liability":    round(total_interest, 2),
            "total_exposure":              round(total_reversal + total_interest, 2),
            "total_itc_re_claimable":      round(total_reclaim, 2),
            "overdue_invoices":    sorted(overdue_list,  key=lambda x: x["itc_to_reverse"], reverse=True),
            "paid_late_invoices":  sorted(paid_late_list,key=lambda x: x["itc_re_claimable"], reverse=True),
            "pending_warnings":    sorted(pending_list,  key=lambda x: x["days_left"]),
            "legal_basis":         "Section 16(2)(b) CGST Act 2017",
            "interest_rate":       "18% per annum (Section 50(3) CGST Act)",
        }

    def validate_itc_chain(self, gstin: str, max_hops: int = 4) -> dict:
        """
        BFS traversal upstream through supply chain to validate ITC eligibility.

        At each hop (supplier of supplier of supplier...):
          - Check if the GSTIN node has any connected MismatchEvent nodes
          - Accumulate eligible vs at-risk ITC

        This models the GST provision that ITC is only valid if the
        ENTIRE upstream chain has paid tax (Section 16(2)(c) CGST Act).

        Returns hop-by-hop chain with blocked nodes highlighted.
        """
        start_node = f"gstin_{gstin}"
        if not self.G.has_node(start_node):
            return {"error": f"GSTIN {gstin} not found in graph"}

        visited   = set()   # BFS cycle prevention
        queue     = deque()
        queue.append((start_node, 0))
        visited.add(start_node)

        hops_data        = []
        total_eligible   = 0.0
        total_at_risk    = 0.0
        blocked_nodes    = []
        chain_risk_scores= []

        while queue:
            node_id, hop = queue.popleft()
            if hop > max_hops:
                break

            node_data = self.G.nodes[node_id]
            if node_data.get("type") != "GSTIN":
                continue

            node_gstin = node_data.get("gstin", "")
            node_name  = node_data.get("name", node_gstin[:15])

            # Find all invoices where this node is RECIPIENT
            hop_invoices = []
            for _, inv_node, edata in self.G.out_edges(node_id, data=True):
                if edata.get("type") == "SUPPLIER_OF":
                    inv_data = self.G.nodes[inv_node]
                    hop_invoices.append(inv_data)

            # Check for mismatches connected to these invoices
            hop_at_risk  = 0.0
            hop_eligible = 0.0
            hop_blocked  = False
            mismatch_types_found = []

            for inv_data in hop_invoices:
                inv_id    = inv_data.get("invoice_id", "")
                inv_mis   = self._mis_by_inv.get(inv_id, [])
                itc_val   = (inv_data.get("igst", 0) +
                             inv_data.get("cgst", 0) +
                             inv_data.get("sgst", 0))

                if inv_mis:
                    critical_mis = any(m["risk_level"] == "CRITICAL" for m in inv_mis)
                    hop_at_risk += sum(m["amount_at_risk"] for m in inv_mis)
                    if critical_mis:
                        hop_blocked = True
                    for m in inv_mis:
                        mismatch_types_found.append(m["mismatch_type"])
                else:
                    hop_eligible += itc_val

            total_eligible  += hop_eligible
            total_at_risk   += hop_at_risk

            # Vendor compliance score
            v_profile = next((v for v in self.vendors if v.get("gstin") == node_gstin), None)
            v_score   = v_profile["composite_risk_score"] if v_profile else 50.0
            chain_risk_scores.append(v_score)

            hop_info = {
                "hop":           hop,
                "gstin":         node_gstin,
                "name":          node_name,
                "invoice_count": len(hop_invoices),
                "itc_eligible":  round(hop_eligible, 2),
                "itc_at_risk":   round(hop_at_risk, 2),
                "status":        "BLOCKED" if hop_blocked else ("AT_RISK" if hop_at_risk > 0 else "CLEAR"),
                "mismatch_types":list(set(mismatch_types_found)),
                "vendor_risk_score": v_score,
            }
            hops_data.append(hop_info)

            if hop_blocked:
                blocked_nodes.append({"hop": hop, "gstin": node_gstin, "name": node_name})

            # BFS — add upstream suppliers (following TRANSACTS_WITH edges backward)
            if hop < max_hops:
                for pred in self.G.predecessors(node_id):
                    if pred not in visited and self.G.nodes[pred].get("type") == "GSTIN":
                        visited.add(pred)
                        queue.append((pred, hop + 1))

        avg_chain_risk = round(sum(chain_risk_scores) / len(chain_risk_scores), 1) if chain_risk_scores else 0
        if avg_chain_risk >= 70 or blocked_nodes:
            chain_risk_level = "CRITICAL"
        elif avg_chain_risk >= 50 or total_at_risk > 0:
            chain_risk_level = "HIGH"
        elif avg_chain_risk >= 30:
            chain_risk_level = "MEDIUM"
        else:
            chain_risk_level = "LOW"

        return {
            "gstin":              gstin,
            "max_hops":           max_hops,
            "hops_traversed":     len(hops_data),
            "total_itc_eligible": round(total_eligible, 2),
            "total_itc_at_risk":  round(total_at_risk, 2),
            "chain_risk_level":   chain_risk_level,
            "blocked_nodes":      blocked_nodes,
            "chain_hops":         hops_data,
        }

    def find_risk_clusters(self) -> list[dict]:
        """
        Build undirected GSTIN transaction subgraph and find connected components.
        Each connected component = a trading cluster.
        Score clusters by average vendor risk score.

        Returns top 10 clusters sorted by cluster risk score (descending).

        Production equivalent:
          Neo4j GDS: gds.louvain.stream() for community detection
          Or: gds.wcc.stream() for weakly connected components
        """
        # Build undirected GSTIN subgraph
        undirected = nx.Graph()
        for u, v, data in self.G.edges(data=True):
            if (data.get("type") == "TRANSACTS_WITH" and
                    self.G.nodes[u].get("type") == "GSTIN" and
                    self.G.nodes[v].get("type") == "GSTIN"):
                undirected.add_edge(u, v,
                    transaction_count=data.get("transaction_count", 0),
                    total_value=data.get("total_value", 0),
                    risk_flag=data.get("risk_flag", False))

        components = list(nx.connected_components(undirected))
        clusters   = []

        # Build vendor risk lookup
        vendor_risk = {v["gstin"]: v["composite_risk_score"] for v in self.vendors}

        for i, component in enumerate(components, 1):
            member_gstins = [self.G.nodes[n].get("gstin", "") for n in component]
            risk_scores   = [vendor_risk.get(g, 50.0) for g in member_gstins]
            avg_risk      = round(sum(risk_scores) / len(risk_scores), 1) if risk_scores else 0
            has_critical  = any(r >= 80 for r in risk_scores)
            total_value   = sum(
                undirected[u][v].get("total_value", 0)
                for u, v in undirected.subgraph(component).edges()
            )

            if avg_risk >= 70:
                cluster_risk = "CRITICAL"
            elif avg_risk >= 50:
                cluster_risk = "HIGH"
            elif avg_risk >= 30:
                cluster_risk = "MEDIUM"
            else:
                cluster_risk = "LOW"

            clusters.append({
                "cluster_id":       f"CLU{i:03d}",
                "member_count":     len(component),
                "member_gstins":    member_gstins[:10],  # top 10 for display
                "avg_risk_score":   avg_risk,
                "max_risk_score":   round(max(risk_scores), 1) if risk_scores else 0,
                "cluster_risk":     cluster_risk,
                "has_critical_member": has_critical,
                "total_transaction_value": round(total_value, 2),
            })

        # Sort by avg risk desc, return top 10
        return sorted(clusters, key=lambda x: x["avg_risk_score"], reverse=True)[:10]

    def get_graph_stats(self) -> dict:
        """Return comprehensive graph statistics."""
        type_counts: dict = defaultdict(int)
        for _, data in self.G.nodes(data=True):
            type_counts[data.get("type", "Unknown")] += 1

        edge_type_counts: dict = defaultdict(int)
        for _, _, data in self.G.edges(data=True):
            edge_type_counts[data.get("type", "Unknown")] += 1

        degrees      = [d for _, d in self.G.degree()]
        avg_degree   = round(sum(degrees) / len(degrees), 2) if degrees else 0
        max_degree   = max(degrees) if degrees else 0

        undirected   = self.G.to_undirected()
        n_components = nx.number_connected_components(undirected)

        return {
            "total_nodes":        self.G.number_of_nodes(),
            "total_edges":        self.G.number_of_edges(),
            "node_type_breakdown":dict(type_counts),
            "edge_type_breakdown":dict(edge_type_counts),
            "avg_degree":         avg_degree,
            "max_degree":         max_degree,
            "connected_components":n_components,
            "is_directed":        True,
            "graph_density":      round(nx.density(self.G), 6),
        }


# ─── Demo ─────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    # Ensure data exists
    if not (DATA_DIR / "invoices.json").exists():
        print("Data files not found. Generating now...")
        sys.path.insert(0, str(Path(__file__).parent))
        from data_generator import generate_all
        generate_all()

    kg = GSTKnowledgeGraph()
    kg.load_data()

    print("\n" + "=" * 60)
    print("  GRAPH STATISTICS")
    print("=" * 60)
    stats = kg.get_graph_stats()
    for k, v in stats.items():
        if isinstance(v, dict):
            print(f"  {k}:")
            for kk, vv in v.items():
                print(f"    {kk:<25} {vv}")
        else:
            print(f"  {k:<30} {v}")

    # Sample reconciliation
    sample_gstin = kg.taxpayers[0]["gstin"] if kg.taxpayers else None
    if sample_gstin:
        print("\n" + "=" * 60)
        print("  SAMPLE RECONCILIATION")
        print("=" * 60)
        result = kg.reconcile_period(sample_gstin, "102024")
        print(f"  GSTIN:          {result['gstin']}")
        print(f"  Period:         {result['period']}")
        print(f"  Total Invoices: {result['total_count']}")
        print(f"  Match Rate:     {result['match_rate']}%")
        print(f"  ITC at Risk:    INR {result['total_itc_at_risk']:,.2f}")
        top_mis = result["classified_mismatches"][:3]
        if top_mis:
            print(f"  Top Mismatches:")
            for m in top_mis:
                print(f"    {m['invoice_id']:12} {m['status']:25} Risk: {m['risk_level']}")

    # ITC chain validation
    if sample_gstin:
        print("\n" + "=" * 60)
        print("  ITC CHAIN VALIDATION")
        print("=" * 60)
        chain = kg.validate_itc_chain(sample_gstin, max_hops=3)
        print(f"  GSTIN:         {chain['gstin']}")
        print(f"  Chain Risk:    {chain['chain_risk_level']}")
        print(f"  ITC Eligible:  INR {chain['total_itc_eligible']:,.2f}")
        print(f"  ITC at Risk:   INR {chain['total_itc_at_risk']:,.2f}")
        print(f"  Blocked Nodes: {len(chain['blocked_nodes'])}")
        for hop in chain["chain_hops"][:4]:
            print(f"  Hop {hop['hop']}: {hop['name'][:30]:<30} {hop['status']}")

    # Risk clusters
    print("\n" + "=" * 60)
    print("  TOP RISK CLUSTERS")
    print("=" * 60)
    clusters = kg.find_risk_clusters()
    for cl in clusters[:5]:
        print(f"  {cl['cluster_id']}: {cl['member_count']} members | "
              f"Avg Risk: {cl['avg_risk_score']:5.1f} | {cl['cluster_risk']}")
