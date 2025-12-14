"""Knowledge Graph module for Null-Lang."""

from .graph_store import GraphStore, InMemoryBackend, SQLiteBackend, Entity, Relationship
from .transaction import Transaction, TransactionManager
from .query_language import QueryEngine, Pattern, QueryResult
from .inference import InferenceEngine, Rule, Fact
from .entity_resolution import EntityResolver
from .superbit_encoder import SuperBitEncoder

__all__ = [
    "GraphStore",
    "InMemoryBackend",
    "SQLiteBackend", 
    "Entity",
    "Relationship",
    "Transaction", 
    "TransactionManager",
    "QueryEngine",
    "Pattern",
    "QueryResult",
    "InferenceEngine",
    "Rule",
    "Fact",
    "EntityResolver",
    "SuperBitEncoder",
]