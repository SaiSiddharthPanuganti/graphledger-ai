# 🏦 GraphLedger AI — Intelligent GST Reconciliation & Risk Intelligence Engine

> **Graph-native ITC reconciliation powered by Neo4j Knowledge Graph Intelligence**

---

## 🎯 Problem Statement

India's GST ITC (Input Tax Credit) reconciliation is fundamentally a **multi-hop graph validation problem**, not a relational table matching problem.

To validate an ITC claim, we must traverse:
```
Taxpayer → Invoice → Vendor → GSTR-1 → GSTR-2B → GSTR-3B → IRN → Payment
```

Traditional SQL JOINs fail to:
- Detect **circular trading** (fake invoice rings)
- Model **vendor risk propagation** across the network
- Run **graph algorithms** (PageRank, community detection)
- Provide **explainable audit trails** with regulatory context

---

## 🏗 Architecture

```
┌─────────────────────────────────┐
│   React Dashboard (Port 5173)   │
│  Executive │ Invoices │ Vendors │
│  Fraud Detection View           │
└──────────────┬──────────────────┘
               │ Axios REST
┌──────────────▼──────────────────┐
│   FastAPI Backend (Port 8000)   │
│  /dashboard  /invoices          │
│  /vendors    /fraud             │
└──────────────┬──────────────────┘
               │ Cypher / In-memory
┌──────────────▼──────────────────┐
│   Knowledge Graph Engine        │
│  Neo4j (Port 7687) OR           │
│  In-Memory Mock (no Neo4j req.) │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│   Risk & Reconciliation Engine  │
│  Multi-hop traversal validation │
│  Rule-based risk scoring        │
│  Fraud pattern detection        │
│  Explainable audit engine       │
└─────────────────────────────────┘
```

---

## 📦 Quick Start (No Docker Required)

### Prerequisites
- Python 3.12+
- Node.js 20+

### 1. Backend Setup
```bash
cd graphledger-ai/backend

# Create virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start API server
uvicorn main:app --reload --port 8000
```

Backend runs at: http://localhost:8000  
API Docs (Swagger): http://localhost:8000/docs

### 2. Frontend Setup
```bash
cd graphledger-ai/frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Dashboard runs at: http://localhost:5173

---

## 🐳 Docker Setup (Full Stack + Neo4j)

```bash
# Start all services
docker-compose up -d

# Services:
#   Neo4j Browser:    http://localhost:7474  (neo4j / graphledger123)
#   FastAPI Backend:  http://localhost:8000
#   React Frontend:   http://localhost:5173
```

---

## 🧠 Knowledge Graph Schema

### Nodes
| Node       | Key Properties |
|------------|---------------|
| `Taxpayer` | gstin, name, state, annual_turnover |
| `Vendor`   | gstin, name, compliance_score, risk_category |
| `Invoice`  | invoice_id, total_gst, period, risk_score, status |
| `IRN`      | irn_number, valid, cancelled |
| `GSTR1`    | period, filed, filing_date |
| `GSTR2B`   | period, total_itc_available |
| `GSTR3B`   | period, itc_claimed, tax_paid |
| `Payment`  | challan_number, amount, status |

### Relationships
```cypher
(Taxpayer)-[:PURCHASED]->(Invoice)
(Invoice)-[:ISSUED_BY]->(Vendor)
(Vendor)-[:FILED]->(GSTR1)
(Invoice)-[:REFLECTED_IN]->(GSTR2B)
(Invoice)-[:CLAIMED_IN]->(GSTR3B)
(Invoice)-[:HAS_IRN]->(IRN)
(Taxpayer)-[:PAID_TAX]->(Payment)
(Vendor)-[:TRANSACTS_WITH]->(Vendor)   ← circular trading detection
```

---

## 🔍 Multi-Hop Reconciliation Logic

Each invoice traverses **6 validation hops**:

```
Hop 1: Taxpayer → Invoice      ✓ Purchase record valid
Hop 2: Invoice → Vendor        ✓ Seller identity verified
Hop 3: Invoice → IRN           ✓/✗ E-invoice mandate check
Hop 4: Invoice → GSTR-2B       ✓/✗ Auto-population check
Hop 5: Vendor → GSTR-1         ✓/✗ Filing compliance check
Hop 6: GSTR-3B → Payment       ✓/✗ Tax deposit confirmation
```

**Risk Scoring (0–100):**
| Failure               | Score | Category |
|-----------------------|-------|----------|
| IRN invalid           | +40   | HIGH     |
| Not in GSTR-2B        | +30   | HIGH     |
| Vendor non-filer      | +35   | CRITICAL |
| Tax unpaid            | +35   | CRITICAL |
| Amount mismatch       | +20   | MEDIUM   |
| Low vendor score      | +10   | HIGH     |

---

## 🚨 Fraud Detection

### A. Circular Trading Detection
- Algorithm: DFS cycle detection on vendor transaction graph
- Neo4j Query: `MATCH cycle=(v:Vendor)-[:TRANSACTS_WITH*3..5]->(v)`
- Demo: V018 → V019 → V020 → V018 (3-node ring)

### B. Suspicious Cluster Detection
- Algorithm: Degree centrality threshold
- Production: Neo4j GDS Louvain community detection
- Flags vendors with unusually high inter-connections

---

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/summary` | Executive KPIs + risk distribution |
| GET | `/invoices` | All invoices with reconciliation status |
| GET | `/invoices/{id}` | Full multi-hop audit report |
| GET | `/vendors` | Vendor compliance profiles |
| GET | `/vendors/{id}` | Detailed vendor risk analysis |
| GET | `/fraud/circular-trading` | Circular trade detection results |
| GET | `/fraud/suspicious-clusters` | Suspicious vendor clusters |
| GET | `/fraud/summary` | Fraud detection summary |

---

## 📁 Project Structure

```
graphledger-ai/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # FastAPI route handlers
│   │   │   ├── dashboard.py     # Executive KPI endpoints
│   │   │   ├── invoices.py      # Invoice reconciliation
│   │   │   ├── vendors.py       # Vendor intelligence
│   │   │   └── fraud.py         # Fraud detection
│   │   └── services/
│   │       ├── mock_data.py         # Synthetic data generator (1T+20V+100I)
│   │       ├── risk_engine.py       # Compliance scoring engine
│   │       ├── reconciliation_engine.py  # Multi-hop traversal
│   │       ├── fraud_detection.py   # Circular trading + clusters
│   │       └── audit_engine.py      # Explainable audit reports
│   ├── cypher/
│   │   ├── schema.cypher        # Neo4j schema + constraints
│   │   └── queries.cypher       # Core traversal queries
│   ├── main.py                  # FastAPI application
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Dashboard.jsx    # Executive summary + charts
│       │   ├── Invoices.jsx     # Invoice table + traversal report
│       │   ├── Vendors.jsx      # Vendor compliance view
│       │   └── FraudDetection.jsx  # Fraud visualization
│       ├── components/          # Reusable UI components
│       └── services/api.js      # Axios API layer
├── docker-compose.yml
└── .env.example
```

---

## 🚀 Scalability Narrative

### Why Graph DB for GST Reconciliation?

| Dimension | SQL Approach | Graph Approach |
|-----------|-------------|----------------|
| Multi-hop joins | O(n²) per hop | O(k) constant |
| Cycle detection | Not natural | Native Cypher |
| Risk propagation | Multiple JOINs | Graph traversal |
| Vendor networks | Slow aggregation | Community detection |
| Fraud patterns | Hard to express | Pattern matching |

### Scale to Millions of Taxpayers

1. **Neo4j Causal Clustering** — horizontal scaling across multiple instances
2. **Graph Partitioning** — state-wise sharding (27 states = 27 partitions)
3. **Streaming Ingestion** — Kafka + Flink for real-time GSTR-1 updates
4. **GDS Algorithms** — PageRank vendor trust scores, Louvain clusters

### ML Enhancement Roadmap

1. **Phase 1 (Current)**: Rule-based scoring (explainable, auditable)
2. **Phase 2**: XGBoost on historical violation patterns
3. **Phase 3**: GraphSAGE (Graph Neural Network) — learns vendor risk from network topology
4. **Phase 4**: Real-time anomaly detection with streaming graph embeddings

### GSTN API Integration (Production)

```python
# Real-world data sources:
# 1. GSTR-2B API: https://services.gst.gov.in/services/auth/api/gstr2b
# 2. GSTIN Validation: https://services.gst.gov.in/services/api/validate
# 3. IRN Verification: https://einvoice1.gst.gov.in/Others/IRNVerification
# 4. E-Way Bill API: https://ewaybillgst.gov.in/apidashboard.aspx
```

---

## 🎤 2-Minute Pitch Script (for Judges)

---

**[0:00 - 0:20] Hook**

> "India's GST system processes 1.5 billion invoices every month.
> Tax authorities issue ₹1.2 lakh crore in ITC disallowance notices annually.
> Why? Because reconciliation today is done with SQL JOINs on flat tables.
> We built something fundamentally different."

**[0:20 - 0:45] Problem + Insight**

> "ITC reconciliation is NOT a table-matching problem — it's a GRAPH problem.
> To validate a single invoice, you must traverse: Taxpayer → Invoice → Vendor → GSTR-1 → GSTR-2B → IRN → Payment.
> Each hop is a potential failure point. SQL can't model this naturally.
> It cannot detect circular trading. It cannot propagate risk through vendor networks."

**[0:45 - 1:10] Solution Demo**

> "GraphLedger AI models the entire GST ecosystem as a Neo4j Knowledge Graph.
> Watch this: [open Invoice view]
> Every invoice goes through 6-hop graph traversal. Failures are detected at each hop.
> Here's an invoice with CRITICAL risk — vendor hasn't filed GSTR-1, IRN is invalid, not in GSTR-2B.
> Our audit engine instantly generates the regulatory citation — Section 16(2)(aa) CGST Act."

**[1:10 - 1:35] Fraud Detection**

> "Now the killer feature — [open Fraud Detection view]
> Our graph engine detected a circular trading ring: ShellCo → Phantom Supplies → Mirage Enterprises → back to ShellCo.
> This 3-node cycle represents ₹[X] crore of fraudulent ITC.
> Detection: one Cypher query. In SQL? Impossible."

**[1:35 - 2:00] Scale + Close**

> "This is an MVP — but the architecture scales.
> Neo4j GDS handles billions of nodes. GraphSAGE can learn fraud patterns from the network.
> With GSTN API integration, this becomes real-time.
> GraphLedger AI — turning India's biggest compliance problem into a graph intelligence problem.
> Thank you."

---

## 📋 Mock Data Summary

| Entity | Count | Details |
|--------|-------|---------|
| Taxpayer | 1 | Mahindra Auto Parts Mfg Ltd, Maharashtra |
| Vendors | 20 | 4 tiers: Excellent/Good/Average/Poor + 3 Fraudulent |
| Invoices | 100 | 30% mismatch scenarios |
| Circular Ring | 1 | 3-vendor cycle (V018→V019→V020→V018) |
| Periods | 6 | Jul–Dec 2024 |
| GSTR-1 Records | ~120 | Per vendor per period |
| GSTR-2B Records | 6 | Per period for buyer |
| GSTR-3B Records | 6 | Per period for buyer |

---

*Built with ❤️ for the GST Hackathon — GraphLedger AI Team*
