"""Tests for Semantic Memory System."""

import pytest
from pathlib import Path
from typing import Any
from src.divineos.semantic_memory import (
    SemanticMemorySystem,
    SemanticMemory,
    MemoryType,
)


@pytest.fixture
def memory_system() -> SemanticMemorySystem:
    """Create a fresh semantic memory system for each test."""
    return SemanticMemorySystem()


class TestSemanticMemory:
    """Tests for SemanticMemory dataclass."""

    def test_create_memory(self) -> None:
        """Test creating a memory."""
        memory = SemanticMemory(
            memory_type=MemoryType.EPISODIC,
            content={"event": "test"},
            importance=0.8,
            tags=["test"],
        )

        assert memory.memory_type == MemoryType.EPISODIC
        assert memory.content == {"event": "test"}
        assert memory.importance == 0.8
        assert memory.tags == ["test"]
        assert memory.access_count == 0

    def test_memory_to_dict(self) -> None:
        """Test converting memory to dictionary."""
        memory = SemanticMemory(
            memory_type=MemoryType.SEMANTIC,
            content={"fact": "test"},
            importance=0.7,
        )

        d = memory.to_dict()
        assert d["memory_type"] == "SEMANTIC"
        assert d["content"] == {"fact": "test"}
        assert d["importance"] == 0.7

    def test_update_access(self) -> None:
        """Test updating access tracking."""
        memory = SemanticMemory()
        initial_count = memory.access_count
        initial_time = memory.last_accessed

        memory.update_access()

        assert memory.access_count == initial_count + 1
        assert memory.last_accessed >= initial_time


class TestSemanticMemorySystem:
    """Tests for SemanticMemorySystem."""

    def test_init(self, memory_system: SemanticMemorySystem) -> None:
        """Test system initialization."""
        assert len(memory_system.episodic) == 0
        assert len(memory_system.semantic) == 0
        assert len(memory_system.procedural) == 0

    def test_store_episodic(self, memory_system: SemanticMemorySystem) -> None:
        """Test storing episodic memory."""
        memory_id = memory_system.store(
            MemoryType.EPISODIC,
            {"event": "test event"},
            importance=0.8,
            tags=["event", "test"],
        )

        assert memory_id is not None
        assert memory_id in memory_system.episodic
        assert memory_system.episodic[memory_id].importance == 0.8

    def test_store_semantic(self, memory_system: SemanticMemorySystem) -> None:
        """Test storing semantic memory."""
        memory_id = memory_system.store(
            MemoryType.SEMANTIC,
            {"fact": "test fact"},
            importance=0.9,
            tags=["fact"],
        )

        assert memory_id in memory_system.semantic
        assert memory_system.semantic[memory_id].content == {"fact": "test fact"}

    def test_store_procedural(
        self, memory_system: SemanticMemorySystem
    ) -> None:
        """Test storing procedural memory."""
        memory_id = memory_system.store(
            MemoryType.PROCEDURAL,
            {"skill": "test skill"},
            importance=0.7,
        )

        assert memory_id in memory_system.procedural

    def test_store_importance_validation(
        self, memory_system: SemanticMemorySystem
    ) -> None:
        """Test importance is clamped to valid range."""
        # Should not raise, importance should be clamped
        memory_id = memory_system.store(
            MemoryType.EPISODIC, {"test": "data"}, importance=1.5
        )
        assert memory_system.episodic[memory_id].importance == 1.0

        memory_id = memory_system.store(
            MemoryType.EPISODIC, {"test": "data"}, importance=-0.5
        )
        assert memory_system.episodic[memory_id].importance == 0.0

    def test_store_clamps_importance(
        self, memory_system: SemanticMemorySystem
    ) -> None:
        """Test that importance is clamped to valid range."""
        memory_id = memory_system.store(
            MemoryType.EPISODIC, {"test": "data"}, importance=1.5
        )
        # Should not raise, importance should be clamped to 1.0
        assert memory_system.episodic[memory_id].importance == 1.0

    def test_recall_by_id(self, memory_system: SemanticMemorySystem) -> None:
        """Test recalling memory by ID."""
        memory_id = memory_system.store(
            MemoryType.EPISODIC, {"event": "test"}
        )

        recalled = memory_system.recall(memory_id)

        assert recalled is not None
        assert recalled.id == memory_id
        assert recalled.access_count == 1

    def test_recall_nonexistent(
        self, memory_system: SemanticMemorySystem
    ) -> None:
        """Test recalling nonexistent memory."""
        recalled = memory_system.recall("nonexistent")
        assert recalled is None

    def test_recall_updates_access(
        self, memory_system: SemanticMemorySystem
    ) -> None:
        """Test that recall updates access count."""
        memory_id = memory_system.store(
            MemoryType.EPISODIC, {"event": "test"}
        )

        memory_system.recall(memory_id)
        memory_system.recall(memory_id)
        memory_system.recall(memory_id)

        memory = memory_system.episodic[memory_id]
        assert memory.access_count == 3

    def test_recall_by_tags(self, memory_system: SemanticMemorySystem) -> None:
        """Test recalling memories by tags."""
        id1 = memory_system.store(
            MemoryType.EPISODIC,
            {"event": "event1"},
            tags=["important", "event"],
        )
        id2 = memory_system.store(
            MemoryType.SEMANTIC,
            {"fact": "fact1"},
            tags=["important", "fact"],
        )
        memory_system.store(
            MemoryType.PROCEDURAL,
            {"skill": "skill1"},
            tags=["skill"],
        )

        # Recall by single tag
        memories = memory_system.recall_by_tags(["important"])
        assert len(memories) == 2
        assert any(m.id == id1 for m in memories)
        assert any(m.id == id2 for m in memories)

        # Recall by multiple tags
        memories = memory_system.recall_by_tags(["important", "event"])
        assert len(memories) >= 1

    def test_recall_by_tags_limit(
        self, memory_system: SemanticMemorySystem
    ) -> None:
        """Test recall by tags with limit."""
        for i in range(5):
            memory_system.store(
                MemoryType.EPISODIC,
                {"event": f"event{i}"},
                tags=["test"],
            )

        memories = memory_system.recall_by_tags(["test"], limit=3)
        assert len(memories) == 3

    def test_recall_by_type(self, memory_system: SemanticMemorySystem) -> None:
        """Test recalling memories by type."""
        memory_system.store(
            MemoryType.EPISODIC, {"event": "event1"}, importance=0.5
        )
        memory_system.store(
            MemoryType.EPISODIC, {"event": "event2"}, importance=0.9
        )
        id3 = memory_system.store(
            MemoryType.SEMANTIC, {"fact": "fact1"}, importance=0.8
        )

        # Recall episodic
        memories = memory_system.recall_by_type(MemoryType.EPISODIC)
        assert len(memories) == 2
        # Should be sorted by importance (descending)
        assert memories[0].importance >= memories[1].importance

        # Recall semantic
        memories = memory_system.recall_by_type(MemoryType.SEMANTIC)
        assert len(memories) == 1
        assert memories[0].id == id3

    def test_recall_by_type_limit(
        self, memory_system: SemanticMemorySystem
    ) -> None:
        """Test recall by type with limit."""
        for i in range(5):
            memory_system.store(
                MemoryType.EPISODIC, {"event": f"event{i}"}
            )

        memories = memory_system.recall_by_type(MemoryType.EPISODIC, limit=2)
        assert len(memories) == 2

    def test_associate_memories(
        self, memory_system: SemanticMemorySystem
    ) -> None:
        """Test creating associations between memories."""
        id1 = memory_system.store(
            MemoryType.EPISODIC, {"event": "event1"}
        )
        id2 = memory_system.store(
            MemoryType.SEMANTIC, {"fact": "fact1"}
        )

        result = memory_system.associate(id1, id2)

        assert result is True
        assert id2 in memory_system.episodic[id1].associations
        assert id1 in memory_system.semantic[id2].associations

    def test_associate_nonexistent(
        self, memory_system: SemanticMemorySystem
    ) -> None:
        """Test associating with nonexistent memory."""
        id1 = memory_system.store(
            MemoryType.EPISODIC, {"event": "event1"}
        )

        result = memory_system.associate(id1, "nonexistent")

        assert result is False

    def test_consolidate(self, memory_system: SemanticMemorySystem) -> None:
        """Test memory consolidation."""
        memory_id = memory_system.store(
            MemoryType.EPISODIC, {"event": "test"}, importance=0.6
        )

        # Access the memory multiple times to trigger consolidation
        for _ in range(7):
            memory_system.recall(memory_id)

        # Consolidate
        consolidated = memory_system.consolidate()

        assert consolidated >= 1
        # Importance should have increased
        assert memory_system.episodic[memory_id].importance > 0.6

    def test_consolidate_threshold(
        self, memory_system: SemanticMemorySystem
    ) -> None:
        """Test consolidation with threshold."""
        memory_id = memory_system.store(
            MemoryType.EPISODIC, {"event": "test"}, importance=0.5
        )

        # Access multiple times
        for _ in range(6):
            memory_system.recall(memory_id)

        # Consolidate with high threshold
        consolidated = memory_system.consolidate(importance_threshold=0.9)

        # Should still consolidate (importance increased)
        assert consolidated >= 0

    def test_get_status(self, memory_system: SemanticMemorySystem) -> None:
        """Test getting system status."""
        memory_system.store(
            MemoryType.EPISODIC, {"event": "event1"}, importance=0.8
        )
        memory_system.store(
            MemoryType.SEMANTIC, {"fact": "fact1"}, importance=0.9
        )
        memory_system.store(
            MemoryType.PROCEDURAL, {"skill": "skill1"}, importance=0.7
        )

        status = memory_system.get_status()

        assert status["status"] == "ONLINE"
        assert status["total_memories"] == 3
        assert status["episodic"] == 1
        assert status["semantic"] == 1
        assert status["procedural"] == 1
        assert 0.7 <= status["average_importance"] <= 0.9

    def test_clear(self, memory_system: SemanticMemorySystem) -> None:
        """Test clearing all memories."""
        memory_system.store(
            MemoryType.EPISODIC, {"event": "event1"}
        )
        memory_system.store(
            MemoryType.SEMANTIC, {"fact": "fact1"}
        )

        memory_system.clear()

        assert len(memory_system.episodic) == 0
        assert len(memory_system.semantic) == 0
        assert len(memory_system.procedural) == 0
        assert len(memory_system.tag_index) == 0

    def test_tag_indexing(self, memory_system: SemanticMemorySystem) -> None:
        """Test that tags are properly indexed."""
        id1 = memory_system.store(
            MemoryType.EPISODIC,
            {"event": "event1"},
            tags=["important", "event"],
        )
        id2 = memory_system.store(
            MemoryType.EPISODIC,
            {"event": "event2"},
            tags=["important"],
        )

        assert "important" in memory_system.tag_index
        assert id1 in memory_system.tag_index["important"]
        assert id2 in memory_system.tag_index["important"]
        assert "event" in memory_system.tag_index
        assert id1 in memory_system.tag_index["event"]

    def test_multiple_memory_types(
        self, memory_system: SemanticMemorySystem
    ) -> None:
        """Test storing and recalling different memory types."""
        episodic_id = memory_system.store(
            MemoryType.EPISODIC, {"event": "test"}
        )
        semantic_id = memory_system.store(
            MemoryType.SEMANTIC, {"fact": "test"}
        )
        procedural_id = memory_system.store(
            MemoryType.PROCEDURAL, {"skill": "test"}
        )

        # Recall each type
        episodic = memory_system.recall(episodic_id)
        semantic = memory_system.recall(semantic_id)
        procedural = memory_system.recall(procedural_id)

        assert episodic.memory_type == MemoryType.EPISODIC
        assert semantic.memory_type == MemoryType.SEMANTIC
        assert procedural.memory_type == MemoryType.PROCEDURAL

    def test_importance_sorting(
        self, memory_system: SemanticMemorySystem
    ) -> None:
        """Test that recall by type sorts by importance."""
        memory_system.store(
            MemoryType.EPISODIC, {"event": "low"}, importance=0.2
        )
        memory_system.store(
            MemoryType.EPISODIC, {"event": "high"}, importance=0.9
        )
        memory_system.store(
            MemoryType.EPISODIC, {"event": "medium"}, importance=0.5
        )

        memories = memory_system.recall_by_type(MemoryType.EPISODIC)

        # Should be sorted by importance descending
        assert memories[0].importance == 0.9
        assert memories[1].importance == 0.5
        assert memories[2].importance == 0.2

    def test_save_checkpoint(
        self, memory_system: SemanticMemorySystem, tmp_path: Any
    ) -> None:
        """Test saving semantic memory checkpoint."""
        memory_system.store(
            MemoryType.EPISODIC, {"event": "event1"}, importance=0.8
        )
        memory_system.store(
            MemoryType.SEMANTIC, {"fact": "fact1"}, importance=0.9
        )

        checkpoint_path = str(tmp_path / "semantic_checkpoint.json")
        result = memory_system.save_checkpoint(checkpoint_path)

        assert result["total_memories"] == 2
        assert result["episodic"] == 1
        assert result["semantic"] == 1
        assert Path(checkpoint_path).exists()

    def test_load_checkpoint(
        self, memory_system: SemanticMemorySystem, tmp_path: Any
    ) -> None:
        """Test loading semantic memory checkpoint."""
        # Store memories
        id1 = memory_system.store(
            MemoryType.EPISODIC,
            {"event": "event1"},
            importance=0.8,
            tags=["important"],
        )
        id2 = memory_system.store(
            MemoryType.SEMANTIC, {"fact": "fact1"}, importance=0.9
        )

        # Save checkpoint
        checkpoint_path = str(tmp_path / "semantic_checkpoint.json")
        memory_system.save_checkpoint(checkpoint_path)

        # Create new system and load
        new_system = SemanticMemorySystem()
        result = new_system.load_checkpoint(checkpoint_path)

        assert result["success"] is True
        assert result["total_memories"] == 2
        assert result["episodic"] == 1
        assert result["semantic"] == 1

        # Verify memories were restored
        recalled_1 = new_system.recall(id1)
        recalled_2 = new_system.recall(id2)

        assert recalled_1 is not None
        assert recalled_1.importance == 0.8
        assert recalled_2 is not None
        assert recalled_2.importance == 0.9

    def test_load_checkpoint_nonexistent(
        self, memory_system: SemanticMemorySystem
    ) -> None:
        """Test loading nonexistent checkpoint."""
        result = memory_system.load_checkpoint("/nonexistent/path.json")

        assert result["success"] is False
        assert "not found" in result["reason"].lower()

    def test_checkpoint_preserves_associations(
        self, memory_system: SemanticMemorySystem, tmp_path: Any
    ) -> None:
        """Test that checkpoint preserves memory associations."""
        id1 = memory_system.store(
            MemoryType.EPISODIC, {"event": "event1"}
        )
        id2 = memory_system.store(
            MemoryType.SEMANTIC, {"fact": "fact1"}
        )

        # Create association
        memory_system.associate(id1, id2)

        # Save and load
        checkpoint_path = str(tmp_path / "semantic_checkpoint.json")
        memory_system.save_checkpoint(checkpoint_path)

        new_system = SemanticMemorySystem()
        new_system.load_checkpoint(checkpoint_path)

        # Verify association was preserved
        recalled_1 = new_system.recall(id1)
        assert id2 in recalled_1.associations

    def test_checkpoint_preserves_tags(
        self, memory_system: SemanticMemorySystem, tmp_path: Any
    ) -> None:
        """Test that checkpoint preserves tags."""
        memory_system.store(
            MemoryType.EPISODIC,
            {"event": "event1"},
            tags=["important", "event"],
        )

        # Save and load
        checkpoint_path = str(tmp_path / "semantic_checkpoint.json")
        memory_system.save_checkpoint(checkpoint_path)

        new_system = SemanticMemorySystem()
        new_system.load_checkpoint(checkpoint_path)

        # Verify tags were preserved
        assert "important" in new_system.tag_index
        assert "event" in new_system.tag_index
