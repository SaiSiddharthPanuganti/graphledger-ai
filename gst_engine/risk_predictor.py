"""
Deliverable 5 — Predictive Vendor Risk Model
=============================================
Graph-pattern based vendor compliance risk predictor.

Uses features extracted from the NetworkX knowledge graph to
predict a vendor's compliance risk for the NEXT filing period.

Feature Engineering:
  - Structural graph features (degree, centrality)
  - Historical mismatch patterns
  - Network risk amplification (contagion from risky neighbors)
  - Filing behavior (streak-based scoring)

Scoring Model:
  Rule-based additive scoring (explainable, auditable)
  Max score: 100 (CRITICAL)

  Phase 2 roadmap:
  - XGBoost trained on 3 years of historical GSTN data
  - Features: same + seasonal patterns, sector benchmarks
  - SHAP values for explainability

  Phase 3 roadmap:
  - GraphSAGE (Graph Neural Network)
  - Learns vendor risk from network topology embeddings
  - Handles cold-start vendors with few transactions
"""

from reconciliation_engine import GSTKnowledgeGraph
from typing import Optional


CATEGORY_THRESHOLDS = {
    "CRITICAL": 80,
    "HIGH":     60,
    "MEDIUM":   40,
    "LOW":      0,
}


def _score_to_category(score: float) -> str:
    if score >= 80: return "CRITICAL"
    if score >= 60: return "HIGH"
    if score >= 40: return "MEDIUM"
    return "LOW"


def _category_order(cat: str) -> int:
    return {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(cat, 0)


class VendorRiskPredictor:
    """
    Predicts next-period vendor compliance risk using graph features.

    Usage:
        kg = GSTKnowledgeGraph()
        kg.load_data()
        predictor = VendorRiskPredictor(kg)
        result = predictor.predict_next_period_risk("29AADCV5678B1ZP")
    """

    def __init__(self, kg: GSTKnowledgeGraph):
        self.kg           = kg
        self.G            = kg.G
        self._vendor_map  = {v["gstin"]: v for v in kg.vendors}
        self._tp_map      = {tp["gstin"]: tp for tp in kg.taxpayers}

    # ----------------------------------------------------------
    # FEATURE EXTRACTION
    # ----------------------------------------------------------

    def compute_graph_features(self, gstin: str) -> dict:
        """
        Extract graph-structural and behavioral features for a GSTIN.

        Features used in risk scoring:
          Structural:   in_degree, out_degree, transaction_volume
          Invoice:      invoice_count, mismatch_count, mismatch_ratio
          Network:      avg_neighbor_risk, network_risk_amplification
          Behavioral:   filing_consistency, has_critical_mismatch
        """
        node_id = f"gstin_{gstin}"
        if not self.G.has_node(node_id):
            return {"error": f"GSTIN {gstin} not in graph"}

        # -- Degree features ------------------------------
        in_degree  = self.G.in_degree(node_id)
        out_degree = self.G.out_degree(node_id)
        tx_volume  = in_degree + out_degree

        # -- Invoice and mismatch counts ------------------
        # Count Invoice nodes reachable via SUPPLIER_OF edges
        invoice_nodes = [
            v for _, v, d in self.G.out_edges(node_id, data=True)
            if d.get("type") == "SUPPLIER_OF"
        ]
        invoice_count = len(invoice_nodes)

        # Count MismatchEvent nodes in 2-hop ego network
        mismatch_count = 0
        has_critical   = False
        for inv_node in invoice_nodes:
            for _, mis_node, d in self.G.out_edges(inv_node, data=True):
                if d.get("type") == "HAS_MISMATCH":
                    mismatch_count += 1
                    mis_data = self.G.nodes[mis_node]
                    if mis_data.get("risk_level") == "CRITICAL":
                        has_critical = True

        mismatch_ratio = mismatch_count / max(1, invoice_count)

        # -- Neighbor risk (contagion) --------------------
        # Average risk of all GSTIN neighbors (suppliers AND buyers)
        neighbor_risks = []
        for neighbor in set(
            list(self.G.predecessors(node_id)) +
            list(self.G.successors(node_id))
        ):
            if self.G.nodes[neighbor].get("type") == "GSTIN":
                n_gstin = self.G.nodes[neighbor].get("gstin", "")
                v_data  = self._vendor_map.get(n_gstin, {})
                if v_data:
                    neighbor_risks.append(v_data.get("composite_risk_score", 50.0))

        avg_neighbor_risk = (
            round(sum(neighbor_risks) / len(neighbor_risks), 1)
            if neighbor_risks else 50.0
        )

        # Network risk amplification:
        # Being connected to risky vendors increases your own risk
        # (Section 16(2)(c) CGST Act — ITC linked to upstream tax payment)
        network_risk_amplification = round(avg_neighbor_risk * 0.3, 1)

        # -- Filing behavior -------------------------------
        tp_data = (self._tp_map.get(gstin) or
                   next((tp for tp in self.kg.taxpayers if tp["gstin"] == gstin), {}))
        filing_streak     = tp_data.get("filing_streak", 0)
        filing_consistency= round(filing_streak / 24, 3)  # Normalized 0–1

        return {
            "gstin":                      gstin,
            "in_degree":                  in_degree,
            "out_degree":                 out_degree,
            "transaction_volume":         tx_volume,
            "invoice_count":              invoice_count,
            "mismatch_count":             mismatch_count,
            "mismatch_ratio":             round(mismatch_ratio, 3),
            "avg_neighbor_risk":          avg_neighbor_risk,
            "network_risk_amplification": network_risk_amplification,
            "filing_consistency":         filing_consistency,
            "filing_streak":              filing_streak,
            "has_critical_mismatch":      has_critical,
        }

    # ----------------------------------------------------------
    # PREDICTION ENGINE
    # ----------------------------------------------------------

    def predict_next_period_risk(self, gstin: str) -> dict:
        """
        Predict compliance risk for the next filing period.

        Scoring rules (additive, capped at 100):
          mismatch_ratio > 0.4    (->) +35  (very high mismatch history)
          mismatch_ratio > 0.2    (->) +15  (moderate mismatch history)
          avg_neighbor_risk > 65  (->) +20  (risky trading network)
          filing_streak < 3       (->) +25  (poor filing history)
          mismatch_count > 5      (->) +15  (many unresolved mismatches)
          has_critical_mismatch   (->) +20  (fraud risk in network)
          filing_streak > 12      (->) -15  (positive: consistent filer)
        """
        features = self.compute_graph_features(gstin)
        if "error" in features:
            return {"error": features["error"]}

        vendor = self._vendor_map.get(gstin, {})
        base_risk = vendor.get("composite_risk_score", 50.0)

        rule_score    = 0
        key_factors   = []

        # -- Rule evaluation ------------------------------
        mr = features["mismatch_ratio"]
        if mr > 0.4:
            rule_score += 35
            key_factors.append(
                f"High mismatch ratio ({mr:.1%}) — 40%+ of invoices have discrepancies"
            )
        elif mr > 0.2:
            rule_score += 15
            key_factors.append(
                f"Moderate mismatch ratio ({mr:.1%}) — requires enhanced monitoring"
            )

        if features["avg_neighbor_risk"] > 65:
            rule_score += 20
            key_factors.append(
                f"High-risk trading partners (avg score {features['avg_neighbor_risk']:.0f}) "
                f"— supply chain contagion risk per Section 16(2)(c)"
            )

        if features["filing_streak"] < 3:
            rule_score += 25
            key_factors.append(
                f"History of late/missed filings (streak: {features['filing_streak']} months) "
                f"— GSTR-1 non-compliance threatens buyer ITC"
            )

        if features["mismatch_count"] > 5:
            rule_score += 15
            key_factors.append(
                f"Multiple unresolved mismatches ({features['mismatch_count']}) "
                f"indicate systemic compliance failure"
            )

        if features["has_critical_mismatch"]:
            rule_score += 20
            key_factors.append(
                "Critical IRN or fraud-related mismatch detected in network "
                "— potential Section 122/132 CGST Act violation"
            )

        if features["filing_streak"] > 12:
            rule_score -= 15
            key_factors.append(
                f"Consistent on-time filing history ({features['filing_streak']} months) "
                f"— reduces predicted risk (positive indicator)"
            )

        # Final score = capped combination of rule-based + base risk
        predicted_score = round(min(100.0, rule_score + base_risk * 0.3 +
                                    features["network_risk_amplification"]), 1)
        predicted_cat   = _score_to_category(predicted_score)

        confidence = "HIGH" if features["invoice_count"] > 10 else "MEDIUM"

        recommendations = {
            "CRITICAL": "Proactively restrict ITC. Initiate vendor audit under Section 65 CGST Act. "
                        "Require bank guarantee for future supplies.",
            "HIGH":     "Enhanced monitoring required. Request compliance certificate before next supply. "
                        "Add GSTR-1 filing clause to purchase contract.",
            "MEDIUM":   "Quarterly review. Flag for reconciliation scrutiny. "
                        "Add to watch list for next GSTR-2B cycle.",
            "LOW":      "Standard processing. Annual review sufficient. "
                        "No immediate action required.",
        }

        return {
            "gstin":                  gstin,
            "vendor_name":            vendor.get("name", "Unknown"),
            "current_risk_score":     base_risk,
            "current_risk_category":  vendor.get("risk_category", "MEDIUM"),
            "predicted_risk_score":   predicted_score,
            "predicted_risk_category":predicted_cat,
            "score_delta":            round(predicted_score - base_risk, 1),
            "confidence":             confidence,
            "key_risk_factors":       key_factors if key_factors else ["No elevated risk factors identified"],
            "graph_features":         features,
            "recommendation":         recommendations[predicted_cat],
        }

    def predict_all_vendors(self) -> dict:
        """
        Run predictions for all GSTINs in the graph.
        Returns sorted list + movement summary (UP/DOWN/STABLE).
        """
        predictions = []
        for vendor in self.kg.vendors:
            result = self.predict_next_period_risk(vendor["gstin"])
            if "error" not in result:
                predictions.append(result)

        predictions.sort(key=lambda x: x["predicted_risk_score"], reverse=True)

        # Movement analysis
        moving_up    = []
        moving_down  = []
        stable       = []
        for p in predictions:
            curr = _category_order(p["current_risk_category"])
            pred = _category_order(p["predicted_risk_category"])
            if pred > curr:
                moving_up.append(p["gstin"])
            elif pred < curr:
                moving_down.append(p["gstin"])
            else:
                stable.append(p["gstin"])

        return {
            "total_vendors":  len(predictions),
            "moving_up":      len(moving_up),    # Risk increasing
            "moving_down":    len(moving_down),  # Risk decreasing
            "stable":         len(stable),
            "predictions":    predictions,
            "alert":          (f"{len(moving_up)} vendors predicted to worsen next period"
                               if moving_up else "No vendors predicted to worsen"),
        }

    def explain_prediction(self, gstin: str) -> str:
        """
        Generate a human-readable prediction explanation paragraph.
        """
        result = self.predict_next_period_risk(gstin)
        if "error" in result:
            return f"Cannot explain prediction: {result['error']}"

        features = result["graph_features"]
        vendor   = self._vendor_map.get(gstin, {})
        name     = vendor.get("name", gstin)
        top_factors = result["key_risk_factors"][:2]
        factors_str = (
            f"'{top_factors[0]}'"
            if len(top_factors) == 1
            else f"'{top_factors[0]}' and '{top_factors[1]}'"
        )

        delta_dir  = "increase" if result["score_delta"] > 0 else "decrease"
        delta_abs  = abs(result["score_delta"])

        explanation = (
            f"Based on graph analysis, {name} (GSTIN: {gstin}) is predicted to be "
            f"{result['predicted_risk_category']} risk in the next filing period "
            f"(predicted score: {result['predicted_risk_score']:.1f}/100, "
            f"a {delta_dir} of {delta_abs:.1f} points from current {result['current_risk_score']:.1f}). "
            f"The primary drivers are {factors_str}. "
            f"Their network of {features['transaction_volume']} trading partner connections "
            f"has an average risk score of {features['avg_neighbor_risk']:.0f}, contributing "
            f"{features['network_risk_amplification']:.1f} additional points via supply chain "
            f"contagion (Section 16(2)(c) CGST Act risk propagation). "
            f"The vendor has filed consistently for {features['filing_streak']} months "
            f"(filing consistency: {features['filing_consistency']:.0%}) with "
            f"{features['mismatch_count']} active mismatches across "
            f"{features['invoice_count']} invoices "
            f"({features['mismatch_ratio']:.1%} mismatch rate). "
            f"Prediction confidence: {result['confidence']}. "
            f"Recommended action: {result['recommendation']}"
        )
        return explanation


# --- Demo -----------------------------------------------------
if __name__ == "__main__":
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).parent))

    kg = GSTKnowledgeGraph()
    kg.load_data()

    predictor = VendorRiskPredictor(kg)

    print("=" * 65)
    print("  VENDOR RISK PREDICTOR — NEXT PERIOD FORECAST")
    print("=" * 65)

    all_result = predictor.predict_all_vendors()
    print(f"\n[Stats] Prediction Summary:")
    print(f"  Total vendors analyzed  : {all_result['total_vendors']}")
    print(f"  Risk increasing ((UP))     : {all_result['moving_up']}")
    print(f"  Risk decreasing ((DN))     : {all_result['moving_down']}")
    print(f"  Stable ((->))              : {all_result['stable']}")
    print(f"  Alert: {all_result['alert']}")

    print(f"\n[CRITICAL] TOP 5 HIGHEST PREDICTED RISK VENDORS:")
    print(f"  {'Vendor':<30} {'Current':>10} {'Predicted':>10} {'Delta':>8} {'Category'}")
    print(f"  {'-'*29} {'-'*10} {'-'*10} {'-'*8} {'-'*8}")
    for p in all_result["predictions"][:5]:
        delta_str = f"+{p['score_delta']:.1f}" if p['score_delta'] > 0 else f"{p['score_delta']:.1f}"
        name_short = p["vendor_name"][:28]
        print(f"  {name_short:<30} {p['current_risk_score']:>10.1f} "
              f"{p['predicted_risk_score']:>10.1f} {delta_str:>8} "
              f"{p['predicted_risk_category']}")

    print(f"\n[Report] VENDORS MOVING TO WORSE RISK CATEGORY:")
    worsening = [p for p in all_result["predictions"]
                 if _category_order(p["predicted_risk_category"]) >
                    _category_order(p["current_risk_category"])]
    if worsening:
        for p in worsening[:5]:
            print(f"  {p['vendor_name'][:35]:<35} "
                  f"{p['current_risk_category']:>8} (->) {p['predicted_risk_category']:<8}")
    else:
        print("  None identified")

    print(f"\n[Table] COMPARISON TABLE (Current vs Predicted — Top 10):")
    print(f"  {'GSTIN':<16} {'Current':>8} {'Predicted':>10} {'Delta':>6}")
    print(f"  {'-'*15} {'-'*8} {'-'*10} {'-'*6}")
    for p in all_result["predictions"][:10]:
        delta_str = f"+{p['score_delta']:.1f}" if p['score_delta'] > 0 else f"{p['score_delta']:.1f}"
        print(f"  {p['gstin']:<16} {p['current_risk_score']:>8.1f} "
              f"{p['predicted_risk_score']:>10.1f} {delta_str:>6}")

    print(f"\n[Note] EXPLANATION (Top Vendor):")
    top_gstin = all_result["predictions"][0]["gstin"]
    print(predictor.explain_prediction(top_gstin))
