"""
chat_engine.py — GraphLedger AI Chatbot Engine
================================================
Groq-powered GST compliance assistant with function calling.
The assistant can query live reconciliation data to answer
questions about invoices, vendors, fraud patterns, and ITC risk.

Architecture:
  User message → Groq LLM (llama-3.3-70b-versatile)
               → [optional] Tool calls → backend data functions
               → Final natural-language response

GST Context embedded in system prompt so the LLM understands
Indian GST terminology without external training.
"""

import json
import os
from typing import Optional

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# ─── Groq client (singleton) ─────────────────────────────────────────────────
_client: Optional[Groq] = None

def get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set in environment")
        _client = Groq(api_key=api_key)
    return _client


# ─── Tool definitions (function calling schema) ───────────────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_dashboard_summary",
            "description": (
                "Returns the live GraphLedger AI dashboard KPIs: total invoices, "
                "mismatches, ITC at risk, match rate, CRITICAL/HIGH/MEDIUM/LOW counts, "
                "and mismatch type breakdown."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_high_risk_invoices",
            "description": (
                "Returns invoices flagged as CRITICAL or HIGH risk. "
                "Use when user asks about risky invoices, ITC denial risk, or mismatches."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "risk_level": {
                        "type": "string",
                        "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
                        "description": "Filter by specific risk level. Default: CRITICAL",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max number of invoices to return (default 5)",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_vendor_risk_report",
            "description": (
                "Returns vendor compliance scores, filing regularity, and risk classification. "
                "Use when user asks about specific vendors or vendor risk."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "vendor_name": {
                        "type": "string",
                        "description": "Partial vendor name to search (optional). If omitted, returns all vendors.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_fraud_alerts",
            "description": (
                "Returns circular trading patterns and suspicious vendor clusters "
                "detected by graph intelligence. Use when user asks about fraud, "
                "circular trading, shell companies, or suspicious patterns."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_itc_reversal_estimate",
            "description": (
                "Calculates total ITC that must be reversed under GST law, "
                "including interest at 18% p.a. for delayed reversal. "
                "Use when user asks about ITC reversal, interest liability, or compliance cost."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "explain_gst_rule",
            "description": (
                "Explains a specific GST rule or legal provision in plain English. "
                "Use when user asks about GST law, sections, rules, or terms."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "rule": {
                        "type": "string",
                        "description": "Rule or term, e.g. 'Section 16(2)(aa)', 'Rule 36(4)', 'GSTR-2B', 'ITC', 'IRN', 'E-Way Bill'",
                    }
                },
                "required": ["rule"],
            },
        },
    },
]


# ─── System prompt ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are GraphBot, the AI assistant embedded in GraphLedger AI — an intelligent GST ITC Reconciliation & Risk Intelligence Engine built for India's GST compliance ecosystem.

## Your Role
You help finance teams, GST officers, and compliance managers:
- Understand their ITC (Input Tax Credit) risk exposure
- Identify mismatch patterns in GSTR-1/2B/3B reconciliation
- Detect fraudulent vendor networks
- Take corrective actions before GST notices arrive

## GST Quick Reference
- **GSTR-1**: Outward supply return filed by SUPPLIER by 11th of next month
- **GSTR-2B**: Auto-populated ITC statement for BUYER generated by GSTN on 14th
- **GSTR-3B**: Monthly summary return filed by BUYER by 20th claiming ITC
- **ITC (Input Tax Credit)**: Tax paid on purchases, claimable against output tax liability
- **IRN**: Invoice Reference Number — 64-char hash, mandatory for B2B invoices ≥ ₹5L
- **Section 16(2)(aa)**: ITC only allowed when invoice appears in buyer's GSTR-2B
- **Rule 36(4)**: ITC capped at 105% of GSTR-2B-eligible ITC
- **Circular Trading**: Fake invoices passed through a ring of companies to claim fraudulent ITC

## Tone
- Be concise, professional, and direct
- Use Indian currency format (₹X.XX Lakh / ₹X Cr)
- Use bold for risk levels (CRITICAL, HIGH, MEDIUM, LOW)
- When citing legal references, use format: Section 16(2)(aa) CGST Act
- Always suggest a remediation action when flagging risk

## Important
- Always call the relevant tool before answering data-related questions
- Never make up invoice numbers, amounts, or vendor names — use tool results
- For non-GST questions, politely redirect to GST/finance topics
"""


# ─── Tool executor (calls actual data functions) ──────────────────────────────
def execute_tool(tool_name: str, args: dict, kg, predictor) -> str:
    """
    Execute a tool call by name. Returns JSON string result.
    kg = GSTKnowledgeGraph instance
    predictor = VendorRiskPredictor instance
    """
    try:
        if tool_name == "get_dashboard_summary":
            from datetime import date, datetime
            mis = kg.mismatches
            total_risk = sum(m["amount_at_risk"] for m in mis)
            by_level = {}
            for m in mis:
                lvl = m["risk_level"]
                by_level[lvl] = by_level.get(lvl, 0) + 1
            overdue_invoices = [
                inv for inv in kg.invoices
                if inv["invoice_id"] not in kg._pay_by_inv
                and (date.today() - datetime.strptime(inv["invoice_date"], "%Y-%m-%d").date()).days > 180
                and (inv["igst"] + inv["cgst"] + inv["sgst"]) > 0
            ]
            overdue_itc = sum(i["igst"] + i["cgst"] + i["sgst"] for i in overdue_invoices)
            return json.dumps({
                "total_invoices": len(kg.invoices),
                "total_mismatches": len(mis),
                "total_itc_at_risk_inr": total_risk,
                "total_itc_at_risk_lakh": round(total_risk / 100000, 2),
                "match_rate_pct": round((1 - len(mis) / max(len(kg.invoices), 1)) * 100, 1),
                "by_risk_level": by_level,
                "vendors_count": len(kg.vendors),
                "critical_vendors": sum(
                    1 for v in kg.vendors
                    if v.get("compliance_score", 100) < 40
                ),
                "payment_overdue_180d_count": len(overdue_invoices),
                "payment_overdue_itc_lakh": round(overdue_itc / 100000, 2),
            })

        elif tool_name == "get_high_risk_invoices":
            risk = args.get("risk_level", "CRITICAL")
            limit = int(args.get("limit", 5))
            mis = [m for m in kg.mismatches if m["risk_level"] == risk]
            mis_sorted = sorted(mis, key=lambda x: x["amount_at_risk"], reverse=True)[:limit]
            return json.dumps({
                "risk_level": risk,
                "count": len(mis),
                "shown": len(mis_sorted),
                "total_itc_at_risk_lakh": round(sum(m["amount_at_risk"] for m in mis) / 100000, 2),
                "invoices": [
                    {
                        "invoice_no": m.get("invoice_no", m.get("invoice_id", "-")),
                        "supplier": m.get("supplier_name", "-"),
                        "supplier_gstin": m.get("supplier_gstin", "-"),
                        "mismatch_type": m.get("mismatch_type", "-"),
                        "amount_at_risk_lakh": round(m["amount_at_risk"] / 100000, 2),
                        "period": m.get("return_period", "-"),
                        "root_cause": m.get("root_cause", "-"),
                        "status": m.get("resolution_status", "-"),
                    }
                    for m in mis_sorted
                ],
            })

        elif tool_name == "get_vendor_risk_report":
            search = args.get("vendor_name", "").lower()
            vendors = list(kg.vendors)
            if search and search not in ("all", ""):
                vendors = [v for v in vendors if search in v.get("name", "").lower()]
            # Sort by compliance_score ascending (worst first)
            vendors = sorted(vendors, key=lambda v: v.get("compliance_score", 100))
            result = []
            for v in vendors[:10]:
                score = v.get("compliance_score", 50)  # score is 0–100
                result.append({
                    "name": v.get("name", v.get("gstin", "-")),
                    "gstin": v.get("gstin", "-"),
                    "compliance_score": round(score, 1),
                    "risk_category": v.get("risk_category", (
                        "CRITICAL" if score < 30 else
                        "HIGH"     if score < 50 else
                        "MEDIUM"   if score < 70 else "LOW"
                    )),
                    "filing_streak_months": v.get("filing_streak", "-"),
                    "mismatch_count": v.get("mismatch_count", 0),
                    "itc_at_risk_lakh": round(v.get("total_itc_at_risk", 0) / 100000, 2),
                    "sector": v.get("sector", "-"),
                })
            return json.dumps({"vendors": result, "total_searched": len(vendors)})

        elif tool_name == "get_fraud_alerts":
            clusters = kg.find_risk_clusters()
            circular = [
                m for m in kg.mismatches
                if "CIRCULAR" in m.get("mismatch_type", "").upper()
            ]
            # High-risk vendors: compliance_score < 30 out of 100
            high_risk_vendors = [
                {"name": v.get("name"), "gstin": v.get("gstin"), "score": v.get("compliance_score")}
                for v in kg.vendors
                if v.get("compliance_score", 100) < 30
            ][:5]
            return json.dumps({
                "circular_trading_flags": len(circular),
                "risk_clusters": clusters[:5],
                "critically_low_score_vendors": high_risk_vendors,
                "note": "Graph-based community detection identifies shell company rings",
            })

        elif tool_name == "get_itc_reversal_estimate":
            mis = kg.mismatches
            critical = [m for m in mis if m["risk_level"] == "CRITICAL"]
            high = [m for m in mis if m["risk_level"] == "HIGH"]
            critical_amt = sum(m["amount_at_risk"] for m in critical)
            high_amt = sum(m["amount_at_risk"] for m in high)
            # 18% p.a. interest for 6 months on critical items
            interest = critical_amt * 0.18 * (6 / 12)
            return json.dumps({
                "must_reverse_immediately_lakh": round(critical_amt / 100000, 2),
                "probable_reversal_lakh": round(high_amt / 100000, 2),
                "interest_liability_lakh": round(interest / 100000, 2),
                "total_exposure_lakh": round((critical_amt + high_amt + interest) / 100000, 2),
                "interest_rate_pct": 18,
                "legal_basis": "Section 50(3) CGST Act — interest on wrongly availed ITC",
            })

        elif tool_name == "explain_gst_rule":
            rule = args.get("rule", "").upper()
            explanations = {
                "SECTION 16(2)(AA)": (
                    "ITC is admissible ONLY when the invoice/debit note appears in the recipient's "
                    "GSTR-2B. Inserted by Finance Act 2021. Effectively makes GSTR-2B the single source "
                    "of truth for ITC eligibility. If your supplier doesn't file GSTR-1, the invoice "
                    "won't appear in your 2B → ITC blocked."
                ),
                "RULE 36(4)": (
                    "Provisional ITC claim is capped at 105% of the ITC appearing in GSTR-2B. "
                    "Any excess provisional ITC must be reversed in GSTR-3B of the same period."
                ),
                "GSTR-1": (
                    "Outward Supplies Return. Filed by SUPPLIER by 11th of next month (quarterly for QRMP). "
                    "Contains invoice-level details which auto-populate buyer's GSTR-2B."
                ),
                "GSTR-2B": (
                    "Auto-populated ITC statement generated by GSTN on 14th of each month. "
                    "Based on suppliers' GSTR-1 filings. Buyer cannot modify it. "
                    "Under Section 16(2)(aa), this is the eligibility gate for ITC."
                ),
                "GSTR-3B": (
                    "Monthly summary return filed by BUYER by 20th. Declares output tax liability "
                    "and ITC claimed. ITC claimed here should match GSTR-2B to avoid notices."
                ),
                "IRN": (
                    "Invoice Reference Number — a unique 64-character hash generated by the IRP "
                    "(Invoice Registration Portal) under e-Invoicing. Mandatory for B2B invoices "
                    "above ₹5 Cr turnover threshold (progressively reduced). Invalid IRN = "
                    "invoice not recognized by GSTN = ITC blocked."
                ),
                "ITC": (
                    "Input Tax Credit — the GST paid on purchases that a business can offset "
                    "against its GST collected on sales. The chain: Supplier collects GST → "
                    "files GSTR-1 → Buyer sees it in GSTR-2B → Buyer claims ITC in GSTR-3B."
                ),
                "E-WAY BILL": (
                    "Electronic waybill required for movement of goods exceeding ₹50,000 in value. "
                    "Generated on ewaybillgst.gov.in. Must be linked to invoice. Missing EWB = "
                    "invoice validity questionable = ITC at risk."
                ),
            }
            # Fuzzy match
            for key, explanation in explanations.items():
                if key in rule or any(word in rule for word in key.split()):
                    return json.dumps({"rule": rule, "explanation": explanation})
            return json.dumps({
                "rule": rule,
                "explanation": (
                    f"I don't have a pre-built explanation for '{rule}'. "
                    "Ask me about: Section 16(2)(aa), Rule 36(4), GSTR-1, GSTR-2B, "
                    "GSTR-3B, IRN, ITC, or E-Way Bill."
                ),
            })

        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

    except Exception as e:
        return json.dumps({"error": str(e)})


# ─── Main chat function ────────────────────────────────────────────────────────
def chat(
    user_message: str,
    history: list[dict],
    kg,
    predictor,
    model: str = "openai/gpt-oss-120b",
) -> tuple[str, list[dict]]:
    """
    Send a message to Groq and return (reply_text, updated_history).

    Uses openai/gpt-oss-120b — OpenAI's model hosted on Groq.
    Excellent function/tool calling reliability (same family as GPT-4o).

    Uses tool_choice="required" for data-related queries so the model MUST
    call a tool instead of hallucinating. Falls back to "auto" for pure
    conversational / GST law explanation messages.
    """
    client = get_client()

    # Force tool use for data queries — prevents the model from hallucinating
    # vendor names / invoice IDs instead of calling the actual tool.
    _DATA_KEYWORDS = {
        "vendor", "invoice", "risk", "critical", "high", "itc", "fraud",
        "circular", "reversal", "summary", "dashboard", "mismatch",
        "compliance", "gstr", "filing", "score", "report", "list",
        "show", "display", "how many", "total", "amount", "lakh", "crore",
    }
    lower_msg = user_message.lower()
    tool_choice = (
        "required"
        if any(kw in lower_msg for kw in _DATA_KEYWORDS)
        else "auto"
    )

    # Build message list: system + history + new user message
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    reply = ""

    # ── Call 1: allow tool use ────────────────────────────────────────────────
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=TOOLS,
        tool_choice=tool_choice,
        max_tokens=1024,
        temperature=0.3,
    )

    assistant_msg = response.choices[0].message
    content = assistant_msg.content or ""

    # Guard: hallucinated <function> tags → no real tool call made
    if "<function>" in content and not assistant_msg.tool_calls:
        reply = (
            "I need to look up live data for that. "
            "Please ensure the backend is running (`python api.py`) and try again."
        )
        messages.append({"role": "assistant", "content": reply})
    elif assistant_msg.tool_calls:
        # Execute every tool call and collect (name, result) pairs
        tool_results: list[tuple[str, str]] = []
        for tc in assistant_msg.tool_calls:
            fn_args = json.loads(tc.function.arguments or "{}")
            result = execute_tool(tc.function.name, fn_args, kg, predictor)
            tool_results.append((tc.function.name, result))

        # ── Call 2: synthesis prompt — NO tool_calls in history ───────────────
        # openai/gpt-oss-120b on Groq will ALWAYS try to call a tool again if
        # the history contains assistant messages with tool_calls — even when
        # tools= is omitted. Fix: build a completely fresh message list that
        # embeds the tool results as plain text so the model has no reason
        # (or ability) to make another tool call.
        data_block = "\n\n".join(
            f"[{name} result]\n{result}" for name, result in tool_results
        )
        synthesis_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            # Keep prior plain-text conversation turns (no tool_calls entries)
            *[
                m for m in messages[1:]
                if m.get("role") in ("user", "assistant")
                and not m.get("tool_calls")
            ],
            {
                "role": "user",
                "content": (
                    f"Original question: {user_message}\n\n"
                    f"Live data retrieved from reconciliation engine:\n{data_block}\n\n"
                    "Using ONLY the data above, provide a clear, well-formatted answer."
                ),
            },
        ]
        response2 = client.chat.completions.create(
            model=model,
            messages=synthesis_messages,
            max_tokens=1024,
            temperature=0.3,
        )
        reply = response2.choices[0].message.content or ""
        messages.append({"role": "assistant", "content": reply})
    else:
        # Model answered directly without needing a tool call
        reply = content
        messages.append({"role": "assistant", "content": reply})
    # ── end ──────────────────────────────────────────────────────────────────

    # Build updated history (exclude system prompt), keep last 20 messages
    # to avoid carrying stale tool exchanges into future turns.
    new_history = messages[1:][-20:]
    return reply, new_history
