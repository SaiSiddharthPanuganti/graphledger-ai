"""Fraud detection endpoints."""
from fastapi import APIRouter
from app.services.fraud_detection import (
    detect_circular_trading,
    detect_suspicious_clusters,
    get_fraud_summary,
)

router = APIRouter()


@router.get("/summary")
def fraud_summary():
    """High-level fraud detection summary."""
    return get_fraud_summary()


@router.get("/circular-trading")
def circular_trading():
    """
    Detect circular trading rings in the vendor knowledge graph.
    Uses DFS cycle detection (mock) / Cypher traversal (Neo4j).
    """
    return detect_circular_trading()


@router.get("/suspicious-clusters")
def suspicious_clusters():
    """
    Identify suspicious vendor clusters using degree centrality.
    Production: Neo4j GDS Louvain community detection algorithm.
    """
    return detect_suspicious_clusters()
