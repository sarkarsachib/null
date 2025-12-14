"""Transaction management with ACID guarantees for knowledge graphs."""

from __future__ import annotations

import json
import logging
import os
import pickle
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, TYPE_CHECKING
from uuid import UUID, uuid4

from .superbit_encoder import SuperBitEncoder

if TYPE_CHECKING:
    from .graph_store import Entity, Relationship, Backend

logger = logging.getLogger(__name__)


@dataclass
class Operation:
    """Represents a single operation within a transaction."""
    operation_id: UUID
    operation_type: str  # CREATE_ENTITY, UPDATE_ENTITY, DELETE_ENTITY, CREATE_RELATIONSHIP, DELETE_RELATIONSHIP
    data: Dict[str, Any]
    timestamp: float = field(default_factory=lambda: time.time())


@dataclass
class TransactionState:
    """Represents the state of a transaction."""
    transaction_id: UUID
    start_time: float
    operations: List[Operation] = field(default_factory=list)
    committed: bool = False
    rolled_back: bool = False
    end_time: Optional[float] = None


class JournalBackend(ABC):
    """Abstract backend for transaction journaling."""
    
    @abstractmethod
    def append_log(self, transaction_id: UUID, operation: Operation) -> None:
        pass
    
    @abstractmethod
    def mark_transaction_committed(self, transaction_id: UUID) -> None:
        pass
    
    @abstractmethod
    def mark_transaction_rolled_back(self, transaction_id: UUID) -> None:
        pass
    
    @abstractmethod
    def get_transaction_operations(self, transaction_id: UUID) -> List[Operation]:
        pass
    
    @abstractmethod
    def list_pending_transactions(self) -> List[UUID]:
        pass
    
    @abstractmethod
    def get_transaction_state(self, transaction_id: UUID) -> Optional[TransactionState]:
        pass


class FileJournalBackend(JournalBackend):
    """File-based journal backend for durability."""
    
    def __init__(self, journal_dir: Union[str, Path]):
        self.journal_dir = Path(journal_dir)
        self.journal_dir.mkdir(parents=True, exist_ok=True)
        
        self._transactions_file = self.journal_dir / "transactions.json"
        self._operations_dir = self.journal_dir / "operations"
        self._operations_dir.mkdir(exist_ok=True)
        
        self._transaction_states: Dict[UUID, TransactionState] = {}
        self._lock = threading.Lock()
        
        self._load_existing_state()
    
    def _load_existing_state(self):
        """Load existing transaction state from disk."""
        if self._transactions_file.exists():
            try:
                with open(self._transactions_file, 'r') as f:
                    data = json.load(f)
                
                for tx_id_str, state_data in data.items():
                    tx_id = UUID(tx_id_str)
                    state = TransactionState(
                        transaction_id=tx_id,
                        start_time=state_data['start_time'],
                        operations=[],
                        committed=state_data.get('committed', False),
                        rolled_back=state_data.get('rolled_back', False),
                        end_time=state_data.get('end_time')
                    )
                    self._transaction_states[tx_id] = state
                    
                    # Load operations for this transaction
                    operations_file = self._operations_dir / f"{tx_id_str}.pkl"
                    if operations_file.exists():
                        with open(operations_file, 'rb') as f:
                            state.operations = pickle.load(f)
                            
            except Exception as e:
                logger.error(f"Failed to load existing transaction state: {e}")
    
    def _save_transaction_state(self, transaction_id: UUID):
        """Save transaction state to disk."""
        state = self._transaction_states[transaction_id]
        states_data = {}
        
        # Load all existing data first
        if self._transactions_file.exists():
            try:
                with open(self._transactions_file, 'r') as f:
                    states_data = json.load(f)
            except:
                pass
        
        # Update this transaction's state
        states_data[str(transaction_id)] = {
            'start_time': state.start_time,
            'committed': state.committed,
            'rolled_back': state.rolled_back,
            'end_time': state.end_time
        }
        
        with open(self._transactions_file, 'w') as f:
            json.dump(states_data, f, indent=2)
    
    def _save_operations(self, transaction_id: UUID):
        """Save operations for a transaction to disk."""
        state = self._transaction_states[transaction_id]
        operations_file = self._operations_dir / f"{str(transaction_id)}.pkl"
        
        with open(operations_file, 'wb') as f:
            pickle.dump(state.operations, f)
    
    def append_log(self, transaction_id: UUID, operation: Operation) -> None:
        with self._lock:
            if transaction_id not in self._transaction_states:
                self._transaction_states[transaction_id] = TransactionState(
                    transaction_id=transaction_id,
                    start_time=time.time()
                )
            
            state = self._transaction_states[transaction_id]
            state.operations.append(operation)
            
            self._save_transaction_state(transaction_id)
            self._save_operations(transaction_id)
    
    def mark_transaction_committed(self, transaction_id: UUID) -> None:
        with self._lock:
            if transaction_id in self._transaction_states:
                state = self._transaction_states[transaction_id]
                state.committed = True
                state.end_time = time.time()
                self._save_transaction_state(transaction_id)
    
    def mark_transaction_rolled_back(self, transaction_id: UUID) -> None:
        with self._lock:
            if transaction_id in self._transaction_states:
                state = self._transaction_states[transaction_id]
                state.rolled_back = True
                state.end_time = time.time()
                self._save_transaction_state(transaction_id)
    
    def get_transaction_operations(self, transaction_id: UUID) -> List[Operation]:
        state = self._transaction_states.get(transaction_id)
        return list(state.operations) if state else []
    
    def list_pending_transactions(self) -> List[UUID]:
        return [
            tx_id for tx_id, state in self._transaction_states.items()
            if not state.committed and not state.rolled_back
        ]
    
    def get_transaction_state(self, transaction_id: UUID) -> Optional[TransactionState]:
        return self._transaction_states.get(transaction_id)


class Transaction:
    """Individual transaction with ACID guarantees."""
    
    def __init__(
        self,
        transaction_id: UUID,
        graph_store: Backend,
        encoder: SuperBitEncoder,
        journal: JournalBackend
    ):
        self.id = transaction_id
        self.graph_store = graph_store
        self.encoder = encoder
        self.journal = journal
        self._pending_operations: List[Operation] = []
        self._local_changes: Dict[str, Any] = {}
        self._completed = False
    
    def upsert_entity(
        self,
        entity_type: str,
        properties: Dict[str, Any],
        entity_id: Optional[UUID] = None,
        embedding: Optional[List[int]] = None
    ) -> Entity:
        """Upsert entity within transaction."""
        if self._completed:
            raise ValueError("Transaction is already completed")
        
        entity_id = entity_id or uuid4()
        
        # Generate Super-Bit embedding if not provided
        if embedding is None:
            embedding = self.encoder.encode_entity(entity_type, properties)
        
        entity = Entity(
            id=entity_id,
            type=entity_type,
            properties=properties,
            superbit_embedding=embedding,
            created_at=time.time(),
            updated_at=time.time()
        )
        
        operation = Operation(
            operation_id=uuid4(),
            operation_type="UPSERT_ENTITY",
            data={
                "entity": {
                    "id": str(entity_id),
                    "type": entity_type,
                    "properties": properties,
                    "superbit_embedding": embedding,
                    "created_at": entity.created_at,
                    "updated_at": entity.updated_at
                }
            }
        )
        
        self._pending_operations.append(operation)
        self.journal.append_log(self.id, operation)
        
        # Store in local changes for rollback capability
        self._local_changes[f"entity_{entity_id}"] = entity
        
        return entity
    
    def create_relationship(
        self,
        source_id: UUID,
        target_id: UUID,
        relationship_type: str,
        properties: Dict[str, Any] = None,
        confidence: float = 1.0
    ) -> Relationship:
        """Create relationship within transaction."""
        if self._completed:
            raise ValueError("Transaction is already completed")
        
        relationship = Relationship(
            id=uuid4(),
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            properties=properties or {},
            confidence=confidence,
            created_at=time.time()
        )
        
        operation = Operation(
            operation_id=uuid4(),
            operation_type="CREATE_RELATIONSHIP",
            data={
                "relationship": {
                    "id": str(relationship.id),
                    "source_id": str(source_id),
                    "target_id": str(target_id),
                    "relationship_type": relationship_type,
                    "properties": properties or {},
                    "confidence": confidence,
                    "created_at": relationship.created_at
                }
            }
        )
        
        self._pending_operations.append(operation)
        self.journal.append_log(self.id, operation)
        
        # Store in local changes for rollback capability
        self._local_changes[f"relationship_{relationship.id}"] = relationship
        
        return relationship
    
    def delete_entity(self, entity_id: UUID, cascade: bool = True) -> bool:
        """Delete entity within transaction."""
        if self._completed:
            raise ValueError("Transaction is already completed")
        
        # Store current state for potential rollback
        existing_entity = self.graph_store.get_entity(entity_id)
        if existing_entity:
            self._local_changes[f"deleted_entity_{entity_id}"] = existing_entity
        
        operation = Operation(
            operation_id=uuid4(),
            operation_type="DELETE_ENTITY",
            data={
                "entity_id": str(entity_id),
                "cascade": cascade
            }
        )
        
        self._pending_operations.append(operation)
        self.journal.append_log(self.id, operation)
        
        return True
    
    def delete_relationship(self, relationship_id: UUID) -> bool:
        """Delete relationship within transaction."""
        if self._completed:
            raise ValueError("Transaction is already completed")
        
        # Store current state for potential rollback
        existing_relationship = self.graph_store.get_relationship(relationship_id)
        if existing_relationship:
            self._local_changes[f"deleted_relationship_{relationship_id}"] = existing_relationship
        
        operation = Operation(
            operation_id=uuid4(),
            operation_type="DELETE_RELATIONSHIP",
            data={
                "relationship_id": str(relationship_id)
            }
        )
        
        self._pending_operations.append(operation)
        self.journal.append_log(self.id, operation)
        
        return True
    
    def commit(self) -> None:
        """Commit transaction with full durability."""
        if self._completed:
            raise ValueError("Transaction is already completed")
        
        try:
            # Apply all operations to the actual graph store
            for operation in self._pending_operations:
                self._apply_operation(operation)
            
            # Mark transaction as committed
            self.journal.mark_transaction_committed(self.id)
            self._completed = True
            
            logger.info(f"Transaction {self.id} committed with {len(self._pending_operations)} operations")
            
        except Exception as e:
            logger.error(f"Failed to commit transaction {self.id}: {e}")
            self.rollback()
            raise
    
    def rollback(self) -> None:
        """Rollback transaction to initial state."""
        if self._completed:
            raise ValueError("Cannot rollback completed transaction")
        
        try:
            # Apply reverse operations to undo changes
            for operation in reversed(self._pending_operations):
                self._reverse_operation(operation)
            
            # Mark transaction as rolled back
            self.journal.mark_transaction_rolled_back(self.id)
            self._completed = True
            
            logger.info(f"Transaction {self.id} rolled back")
            
        except Exception as e:
            logger.error(f"Failed to rollback transaction {self.id}: {e}")
            raise
    
    def _apply_operation(self, operation: Operation) -> None:
        """Apply a single operation to the graph store."""
        data = operation.data
        
        if operation.operation_type == "UPSERT_ENTITY":
            entity_data = data["entity"]
            entity = Entity(
                id=UUID(entity_data["id"]),
                type=entity_data["type"],
                properties=entity_data["properties"],
                superbit_embedding=entity_data["superbit_embedding"],
                created_at=entity_data["created_at"],
                updated_at=entity_data["updated_at"]
            )
            self.graph_store.store_entity(entity)
            
        elif operation.operation_type == "CREATE_RELATIONSHIP":
            rel_data = data["relationship"]
            relationship = Relationship(
                id=UUID(rel_data["id"]),
                source_id=UUID(rel_data["source_id"]),
                target_id=UUID(rel_data["target_id"]),
                relationship_type=rel_data["relationship_type"],
                properties=rel_data["properties"],
                confidence=rel_data["confidence"],
                created_at=rel_data["created_at"]
            )
            self.graph_store.store_relationship(relationship)
            
        elif operation.operation_type == "DELETE_ENTITY":
            entity_id = UUID(data["entity_id"])
            cascade = data.get("cascade", True)
            
            if cascade:
                # Delete all relationships involving this entity
                out_rels = self.graph_store.get_relationships_by_source(entity_id)
                in_rels = self.graph_store.get_relationships_by_target(entity_id)
                
                for rel in out_rels + in_rels:
                    self.graph_store.delete_relationship(rel.id)
            
            self.graph_store.delete_entity(entity_id)
            
        elif operation.operation_type == "DELETE_RELATIONSHIP":
            relationship_id = UUID(data["relationship_id"])
            self.graph_store.delete_relationship(relationship_id)
    
    def _reverse_operation(self, operation: Operation) -> None:
        """Reverse a single operation."""
        data = operation.data
        
        if operation.operation_type == "UPSERT_ENTITY":
            # For upsert, we need to restore the previous state
            entity_data = data["entity"]
            entity_id = UUID(entity_data["id"])
            
            # Check if entity existed before
            original_entity = self._local_changes.get(f"deleted_entity_{entity_id}")
            if original_entity:
                self.graph_store.store_entity(original_entity)
            else:
                # Entity is new, remove it
                self.graph_store.delete_entity(entity_id, cascade=False)
            
        elif operation.operation_type == "CREATE_RELATIONSHIP":
            # Remove the created relationship
            rel_data = data["relationship"]
            relationship_id = UUID(rel_data["id"])
            self.graph_store.delete_relationship(relationship_id)
            
        elif operation.operation_type == "DELETE_ENTITY":
            # Restore the deleted entity
            entity_id = UUID(data["entity_id"])
            deleted_entity = self._local_changes.get(f"deleted_entity_{entity_id}")
            if deleted_entity:
                self.graph_store.store_entity(deleted_entity)
            
        elif operation.operation_type == "DELETE_RELATIONSHIP":
            # Restore the deleted relationship
            relationship_id = UUID(data["relationship_id"])
            deleted_relationship = self._local_changes.get(f"deleted_relationship_{relationship_id}")
            if deleted_relationship:
                self.graph_store.store_relationship(deleted_relationship)


class TransactionManager:
    """Manages transactions with ACID guarantees and crash recovery."""
    
    def __init__(
        self,
        journal_backend: Optional[JournalBackend] = None,
        graph_store: Optional[Backend] = None,
        encoder: Optional[SuperBitEncoder] = None
    ):
        self.journal_backend = journal_backend or FileJournalBackend("./journal")
        self.graph_store = graph_store
        self.encoder = encoder or SuperBitEncoder()
        self._active_transactions: Dict[UUID, Transaction] = {}
        self._lock = threading.Lock()
    
    def begin_transaction(self) -> Transaction:
        """Begin a new transaction."""
        transaction_id = uuid4()
        
        if not self.graph_store:
            raise ValueError("Graph store not configured")
        
        transaction = Transaction(
            transaction_id=transaction_id,
            graph_store=self.graph_store,
            encoder=self.encoder,
            journal=self.journal_backend
        )
        
        with self._lock:
            self._active_transactions[transaction_id] = transaction
        
        logger.debug(f"Started transaction {transaction_id}")
        return transaction
    
    def commit_transaction(self, transaction: Transaction) -> None:
        """Commit a transaction."""
        with self._lock:
            if transaction.id not in self._active_transactions:
                raise ValueError(f"Transaction {transaction.id} not found")
            
            transaction.commit()
            del self._active_transactions[transaction.id]
    
    def rollback_transaction(self, transaction: Transaction) -> None:
        """Rollback a transaction."""
        with self._lock:
            if transaction.id not in self._active_transactions:
                raise ValueError(f"Transaction {transaction.id} not found")
            
            transaction.rollback()
            del self._active_transactions[transaction.id]
    
    def recover_transactions(self) -> Dict[str, int]:
        """Recover pending transactions after crash."""
        logger.info("Starting transaction recovery...")
        
        recovered_committed = 0
        recovered_rolled_back = 0
        
        pending_transactions = self.journal_backend.list_pending_transactions()
        
        for transaction_id in pending_transactions:
            state = self.journal_backend.get_transaction_state(transaction_id)
            if state:
                logger.info(f"Recovering transaction {transaction_id}")
                
                try:
                    # Try to reapply the transaction
                    if self.graph_store:
                        transaction = Transaction(
                            transaction_id=transaction_id,
                            graph_store=self.graph_store,
                            encoder=self.encoder,
                            journal=self.journal_backend
                        )
                        
                        for operation in state.operations:
                            transaction._apply_operation(operation)
                        
                        self.journal_backend.mark_transaction_committed(transaction_id)
                        recovered_committed += 1
                        
                except Exception as e:
                    logger.error(f"Failed to recover transaction {transaction_id}: {e}")
                    self.journal_backend.mark_transaction_rolled_back(transaction_id)
                    recovered_rolled_back += 1
        
        logger.info(f"Recovery complete: {recovered_committed} committed, {recovered_rolled_back} rolled back")
        
        return {
            "recovered_committed": recovered_committed,
            "recovered_rolled_back": recovered_rolled_back
        }
    
    def list_active_transactions(self) -> List[UUID]:
        """List currently active transactions."""
        with self._lock:
            return list(self._active_transactions.keys())
    
    def get_transaction(self, transaction_id: UUID) -> Optional[Transaction]:
        """Get a transaction by ID."""
        with self._lock:
            return self._active_transactions.get(transaction_id)