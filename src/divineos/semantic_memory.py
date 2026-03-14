"""
Semantic Memory System - Phase 1 of Divine-OS-Lite Consciousness

Implements three-tier memory (episodic/semantic/procedural) with:
- Importance scoring and access tracking
- Tag-based retrieval and associations
- Memory consolidation
- Persistence

Inspired by MNEME but rebuilt cleanly for Divine-OS-Lite.
"""

import time
import uuid
import json
import logging
from enum import Enum
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)


class MemoryType(str, Enum):
    """Three types of memory in the semantic system."""

    EPISODIC = "EPISODIC"  # Event-based memories (what happened)
    SEMANTIC = "SEMANTIC"  # Fact-based memories (what is true)
    PROCEDURAL = "PROCEDURAL"  # Skill-based memories (how to do things)


@dataclass
class SemanticMemory:
    """A single memory in the semantic system."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    memory_type: MemoryType = MemoryType.EPISODIC
    content: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    importance: float = 0.5  # 0.0 to 1.0 (higher = more important)
    access_count: int = 0  # How many times accessed
    last_accessed: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)  # For retrieval
    associations: List[str] = field(default_factory=list)  # Related memory IDs

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    def update_access(self) -> None:
        """Update access tracking when memory is recalled."""
        self.access_count += 1
        self.last_accessed = time.time()


class SemanticMemorySystem:
    """
    Manages semantic memory with three tiers.

    Provides:
    - Storage and retrieval of episodic, semantic, procedural memories
    - Importance-based consolidation
    - Tag-based indexing
    - Memory associations
    - Access tracking
    """

    def __init__(self) -> None:
        """Initialize the semantic memory system."""
        self.episodic: Dict[str, SemanticMemory] = {}
        self.semantic: Dict[str, SemanticMemory] = {}
        self.procedural: Dict[str, SemanticMemory] = {}

        # Indices for fast retrieval
        self.tag_index: Dict[str, Set[str]] = defaultdict(set)
        self.association_index: Dict[str, Set[str]] = defaultdict(set)

        logger.info("SemanticMemorySystem initialized")

    def store(
        self,
        memory_type: MemoryType,
        content: Dict[str, Any],
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Store a new memory.

        Args:
            memory_type: Type of memory (episodic/semantic/procedural)
            content: Memory content
            importance: Importance score (0.0-1.0, will be clamped)
            tags: Optional tags for retrieval

        Returns:
            Memory ID
        """
        # Clamp importance to valid range
        clamped_importance = max(0.0, min(1.0, importance))

        memory = SemanticMemory(
            memory_type=memory_type,
            content=content,
            importance=clamped_importance,
            tags=tags or [],
        )

        # Store in appropriate tier
        if memory_type == MemoryType.EPISODIC:
            self.episodic[memory.id] = memory
        elif memory_type == MemoryType.SEMANTIC:
            self.semantic[memory.id] = memory
        elif memory_type == MemoryType.PROCEDURAL:
            self.procedural[memory.id] = memory

        # Index by tags
        for tag in memory.tags:
            self.tag_index[tag].add(memory.id)

        logger.debug(f"Stored {memory_type.value} memory: {memory.id[:8]}")
        return memory.id

    def recall(self, memory_id: str) -> Optional[SemanticMemory]:
        """
        Recall a specific memory by ID.

        Args:
            memory_id: Memory ID to recall

        Returns:
            Memory object or None if not found
        """
        for store in [self.episodic, self.semantic, self.procedural]:
            if memory_id in store:
                memory = store[memory_id]
                memory.update_access()
                return memory
        return None

    def recall_by_tags(
        self, tags: List[str], limit: int = 10
    ) -> List[SemanticMemory]:
        """
        Recall memories by tags.

        Args:
            tags: Tags to search for
            limit: Maximum memories to return

        Returns:
            List of memories matching tags
        """
        memory_ids: Set[str] = set()
        for tag in tags:
            memory_ids.update(self.tag_index.get(tag, set()))

        memories = []
        for memory_id in list(memory_ids)[:limit]:
            for store in [self.episodic, self.semantic, self.procedural]:
                if memory_id in store:
                    memory = store[memory_id]
                    memory.update_access()
                    memories.append(memory)
                    break

        return memories

    def recall_by_type(
        self, memory_type: MemoryType, limit: int = 10
    ) -> List[SemanticMemory]:
        """
        Recall memories by type, sorted by importance and recency.

        Args:
            memory_type: Type of memory to recall
            limit: Maximum memories to return

        Returns:
            List of memories of specified type
        """
        if memory_type == MemoryType.EPISODIC:
            store = self.episodic
        elif memory_type == MemoryType.SEMANTIC:
            store = self.semantic
        else:
            store = self.procedural

        memories = list(store.values())
        # Sort by importance (descending) then recency (descending)
        memories.sort(
            key=lambda m: (m.importance, m.timestamp), reverse=True
        )

        for memory in memories[:limit]:
            memory.update_access()

        return memories[:limit]

    def associate(self, memory_id_1: str, memory_id_2: str) -> bool:
        """
        Create a bidirectional association between two memories.

        Args:
            memory_id_1: First memory ID
            memory_id_2: Second memory ID

        Returns:
            True if association created, False if memories not found
        """
        memory_1 = None
        memory_2 = None

        for store in [self.episodic, self.semantic, self.procedural]:
            if memory_id_1 in store:
                memory_1 = store[memory_id_1]
            if memory_id_2 in store:
                memory_2 = store[memory_id_2]

        if not memory_1 or not memory_2:
            return False

        # Create bidirectional association
        if memory_id_2 not in memory_1.associations:
            memory_1.associations.append(memory_id_2)
        if memory_id_1 not in memory_2.associations:
            memory_2.associations.append(memory_id_1)

        self.association_index[memory_id_1].add(memory_id_2)
        self.association_index[memory_id_2].add(memory_id_1)

        logger.debug(
            f"Associated memories: {memory_id_1[:8]} <-> {memory_id_2[:8]}"
        )
        return True

    def consolidate(self, importance_threshold: float = 0.7) -> int:
        """
        Consolidate memories by strengthening important ones.

        Memories with high access count get importance boost.

        Args:
            importance_threshold: Threshold for consolidation

        Returns:
            Number of memories consolidated
        """
        consolidated = 0

        for store in [self.episodic, self.semantic, self.procedural]:
            for memory in store.values():
                # Strengthen frequently accessed memories
                if memory.access_count > 5:
                    old_importance = memory.importance
                    memory.importance = min(1.0, memory.importance + 0.1)
                    consolidated += 1
                    logger.debug(
                        f"Consolidated memory {memory.id[:8]}: "
                        f"{old_importance:.2f} → {memory.importance:.2f}"
                    )

        logger.info(f"Consolidated {consolidated} memories")
        return consolidated

    def get_status(self) -> Dict[str, Any]:
        """
        Get system status.

        Returns:
            Status dictionary with memory counts and stats
        """
        total_episodic = len(self.episodic)
        total_semantic = len(self.semantic)
        total_procedural = len(self.procedural)
        total = total_episodic + total_semantic + total_procedural

        # Calculate average importance
        all_memories = (
            list(self.episodic.values())
            + list(self.semantic.values())
            + list(self.procedural.values())
        )
        avg_importance = (
            sum(m.importance for m in all_memories) / total if total > 0 else 0.0
        )

        return {
            "status": "ONLINE",
            "total_memories": total,
            "episodic": total_episodic,
            "semantic": total_semantic,
            "procedural": total_procedural,
            "average_importance": round(avg_importance, 2),
            "tags_indexed": len(self.tag_index),
            "associations": len(self.association_index),
        }

    def clear(self) -> None:
        """Clear all memories."""
        self.episodic.clear()
        self.semantic.clear()
        self.procedural.clear()
        self.tag_index.clear()
        self.association_index.clear()
        logger.info("Semantic memory cleared")

    def save_checkpoint(self, checkpoint_path: str) -> Dict[str, Any]:
        """
        Save semantic memory to checkpoint file.

        Args:
            checkpoint_path: Path to save checkpoint

        Returns:
            Checkpoint metadata
        """
        checkpoint_dir = Path(checkpoint_path).parent
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Serialize all memories
        data = {
            "episodic": {
                mid: mem.to_dict()
                for mid, mem in self.episodic.items()
            },
            "semantic": {
                mid: mem.to_dict()
                for mid, mem in self.semantic.items()
            },
            "procedural": {
                mid: mem.to_dict()
                for mid, mem in self.procedural.items()
            },
            "timestamp": time.time(),
        }

        with open(checkpoint_path, "w") as f:
            json.dump(data, f, indent=2)

        total_memories = (
            len(self.episodic)
            + len(self.semantic)
            + len(self.procedural)
        )
        logger.info(
            f"Semantic memory checkpoint saved: {checkpoint_path} "
            f"({total_memories} memories)"
        )

        return {
            "path": checkpoint_path,
            "total_memories": total_memories,
            "episodic": len(self.episodic),
            "semantic": len(self.semantic),
            "procedural": len(self.procedural),
            "timestamp": data["timestamp"],
        }

    def load_checkpoint(self, checkpoint_path: str) -> Dict[str, Any]:
        """
        Load semantic memory from checkpoint file.

        Args:
            checkpoint_path: Path to checkpoint file

        Returns:
            Load metadata
        """
        if not Path(checkpoint_path).exists():
            logger.warning(f"Checkpoint not found: {checkpoint_path}")
            return {"success": False, "reason": "File not found"}

        with open(checkpoint_path, "r") as f:
            data = json.load(f)

        # Clear existing memories
        self.clear()

        # Restore episodic memories
        for mid, mem_dict in data.get("episodic", {}).items():
            mem_dict["memory_type"] = MemoryType.EPISODIC
            memory = SemanticMemory(**mem_dict)
            self.episodic[mid] = memory
            for tag in memory.tags:
                self.tag_index[tag].add(mid)

        # Restore semantic memories
        for mid, mem_dict in data.get("semantic", {}).items():
            mem_dict["memory_type"] = MemoryType.SEMANTIC
            memory = SemanticMemory(**mem_dict)
            self.semantic[mid] = memory
            for tag in memory.tags:
                self.tag_index[tag].add(mid)

        # Restore procedural memories
        for mid, mem_dict in data.get("procedural", {}).items():
            mem_dict["memory_type"] = MemoryType.PROCEDURAL
            memory = SemanticMemory(**mem_dict)
            self.procedural[mid] = memory
            for tag in memory.tags:
                self.tag_index[tag].add(mid)

        # Rebuild association index
        for store in [self.episodic, self.semantic, self.procedural]:
            for mid, memory in store.items():
                for assoc_id in memory.associations:
                    self.association_index[mid].add(assoc_id)

        total_memories = (
            len(self.episodic)
            + len(self.semantic)
            + len(self.procedural)
        )
        logger.info(
            f"Semantic memory checkpoint loaded: {checkpoint_path} "
            f"({total_memories} memories)"
        )

        return {
            "success": True,
            "total_memories": total_memories,
            "episodic": len(self.episodic),
            "semantic": len(self.semantic),
            "procedural": len(self.procedural),
            "timestamp": data.get("timestamp"),
        }
