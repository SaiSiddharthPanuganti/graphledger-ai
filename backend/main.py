"""
GraphLedger AI — FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import dashboard, invoices, vendors, fraud
from app.services.mock_data import store

app = FastAPI(
    title="GraphLedger AI — GST Reconciliation Engine",
    description=(
        "Intelligent GST ITC Reconciliation using Knowledge Graph Intelligence. "
        "Models the GST ecosystem as a Neo4j knowledge graph and performs "
        "multi-hop traversal validation, risk scoring, and fraud detection."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize mock data on startup
@app.on_event("startup")
async def startup_event():
    store.initialize()
    print("✅ GraphLedger AI backend started. Mock data loaded.")

# Register routers
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(invoices.router,  prefix="/invoices",  tags=["Invoices"])
app.include_router(vendors.router,   prefix="/vendors",   tags=["Vendors"])
app.include_router(fraud.router,     prefix="/fraud",     tags=["Fraud Detection"])

@app.get("/", tags=["Health"])
def root():
    return {
        "product": "GraphLedger AI",
        "status":  "running",
        "version": "1.0.0",
        "graph_engine": "Neo4j Knowledge Graph (Mock Mode)",
        "docs": "/docs",
    }

@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy", "data_loaded": store._initialized}
