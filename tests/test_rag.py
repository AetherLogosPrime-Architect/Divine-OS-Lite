"""Tests for RAG (Retrieval-Augmented Generation) module."""

import tempfile
from pathlib import Path

import pytest

from src.divineos.rag import (
    Document,
    DocumentStore,
    RAG,
    RetrievalResult,
    SimpleRetriever,
)


class TestDocument:
    """Tests for Document class."""

    def test_init(self) -> None:
        """Test document initialization."""
        doc = Document(content="Test content", source="test.txt")
        assert doc.content == "Test content"
        assert doc.source == "test.txt"
        assert doc.doc_id
        assert doc.created_at

    def test_init_with_metadata(self) -> None:
        """Test document with metadata."""
        metadata = {"author": "test", "version": "1.0"}
        doc = Document(
            content="Test content", source="test.txt", metadata=metadata
        )
        assert doc.metadata == metadata

    def test_init_empty_content_raises(self) -> None:
        """Test that empty content raises error."""
        with pytest.raises(ValueError, match="content cannot be empty"):
            Document(content="", source="test.txt")

    def test_init_empty_source_raises(self) -> None:
        """Test that empty source raises error."""
        with pytest.raises(ValueError, match="source cannot be empty"):
            Document(content="Test", source="")

    def test_chunk_simple(self) -> None:
        """Test simple document chunking."""
        content = "word1 word2 word3 word4 word5"
        doc = Document(content=content, source="test.txt", chunk_size=10)
        chunks = doc.chunk()
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)

    def test_chunk_large_document(self) -> None:
        """Test chunking large document."""
        content = " ".join(["word"] * 100)
        doc = Document(content=content, source="test.txt", chunk_size=50)
        chunks = doc.chunk()
        assert len(chunks) > 1
        assert all(len(chunk) <= 100 for chunk in chunks)

    def test_to_dict(self) -> None:
        """Test document to dictionary conversion."""
        doc = Document(content="Test", source="test.txt")
        doc_dict = doc.to_dict()
        assert doc_dict["content"] == "Test"
        assert doc_dict["source"] == "test.txt"
        assert "doc_id" in doc_dict
        assert "created_at" in doc_dict


class TestRetrievalResult:
    """Tests for RetrievalResult class."""

    def test_init(self) -> None:
        """Test retrieval result initialization."""
        docs = [Document(content="Test", source="test.txt")]
        result = RetrievalResult(
            documents=docs, scores=[0.9], query="test", total_retrieved=1
        )
        assert result.total_retrieved == 1
        assert len(result.documents) == 1

    def test_get_top_k(self) -> None:
        """Test getting top k documents."""
        docs = [
            Document(content="Test1", source="test1.txt"),
            Document(content="Test2", source="test2.txt"),
            Document(content="Test3", source="test3.txt"),
        ]
        result = RetrievalResult(
            documents=docs, scores=[0.5, 0.9, 0.7], query="test", total_retrieved=3
        )
        top_2 = result.get_top_k(2)
        assert len(top_2) == 2
        assert top_2[0].content == "Test2"

    def test_get_context_text(self) -> None:
        """Test getting context text."""
        docs = [
            Document(content="Content1", source="test1.txt"),
            Document(content="Content2", source="test2.txt"),
        ]
        result = RetrievalResult(
            documents=docs, scores=[0.9, 0.8], query="test", total_retrieved=2
        )
        context = result.get_context_text(k=2)
        assert "Content1" in context
        assert "Content2" in context
        assert "test1.txt" in context

    def test_get_context_text_empty(self) -> None:
        """Test getting context text with no documents."""
        result = RetrievalResult(
            documents=[], scores=[], query="test", total_retrieved=0
        )
        context = result.get_context_text()
        assert context == ""


class TestDocumentStore:
    """Tests for DocumentStore class."""

    def test_init(self) -> None:
        """Test document store initialization."""
        store = DocumentStore()
        assert len(store.documents) == 0
        assert len(store.source_index) == 0

    def test_add_document(self) -> None:
        """Test adding document."""
        store = DocumentStore()
        doc = Document(content="Test", source="test.txt")
        doc_id = store.add_document(doc)
        assert doc_id in store.documents
        assert "test.txt" in store.source_index

    def test_get_document(self) -> None:
        """Test getting document."""
        store = DocumentStore()
        doc = Document(content="Test", source="test.txt")
        doc_id = store.add_document(doc)
        retrieved = store.get_document(doc_id)
        assert retrieved is not None
        assert retrieved.content == "Test"

    def test_get_document_not_found(self) -> None:
        """Test getting non-existent document."""
        store = DocumentStore()
        result = store.get_document("nonexistent")
        assert result is None

    def test_get_documents_by_source(self) -> None:
        """Test getting documents by source."""
        store = DocumentStore()
        doc1 = Document(content="Test1", source="test.txt")
        doc2 = Document(content="Test2", source="test.txt")
        store.add_document(doc1)
        store.add_document(doc2)
        docs = store.get_documents_by_source("test.txt")
        assert len(docs) == 2

    def test_remove_document(self) -> None:
        """Test removing document."""
        store = DocumentStore()
        doc = Document(content="Test", source="test.txt")
        doc_id = store.add_document(doc)
        removed = store.remove_document(doc_id)
        assert removed is True
        assert doc_id not in store.documents

    def test_remove_document_not_found(self) -> None:
        """Test removing non-existent document."""
        store = DocumentStore()
        removed = store.remove_document("nonexistent")
        assert removed is False

    def test_get_all_documents(self) -> None:
        """Test getting all documents."""
        store = DocumentStore()
        doc1 = Document(content="Test1", source="test1.txt")
        doc2 = Document(content="Test2", source="test2.txt")
        store.add_document(doc1)
        store.add_document(doc2)
        all_docs = store.get_all_documents()
        assert len(all_docs) == 2

    def test_clear(self) -> None:
        """Test clearing store."""
        store = DocumentStore()
        doc = Document(content="Test", source="test.txt")
        store.add_document(doc)
        store.clear()
        assert len(store.documents) == 0
        assert len(store.source_index) == 0

    def test_get_stats(self) -> None:
        """Test getting store statistics."""
        store = DocumentStore()
        doc1 = Document(content="Test1", source="test1.txt")
        doc2 = Document(content="Test2", source="test2.txt")
        store.add_document(doc1)
        store.add_document(doc2)
        stats = store.get_stats()
        assert stats["total_documents"] == 2
        assert stats["total_sources"] == 2


class TestSimpleRetriever:
    """Tests for SimpleRetriever class."""

    def test_init(self) -> None:
        """Test retriever initialization."""
        store = DocumentStore()
        retriever = SimpleRetriever(store)
        assert retriever.store is store

    def test_retrieve_empty_store(self) -> None:
        """Test retrieval from empty store."""
        store = DocumentStore()
        retriever = SimpleRetriever(store)
        result = retriever.retrieve("test")
        assert result.total_retrieved == 0

    def test_retrieve_single_document(self) -> None:
        """Test retrieving single document."""
        store = DocumentStore()
        doc = Document(content="test content", source="test.txt")
        store.add_document(doc)
        retriever = SimpleRetriever(store)
        result = retriever.retrieve("test")
        assert result.total_retrieved == 1
        assert result.documents[0].content == "test content"

    def test_retrieve_multiple_documents(self) -> None:
        """Test retrieving multiple documents."""
        store = DocumentStore()
        doc1 = Document(content="test content one", source="test1.txt")
        doc2 = Document(content="test content two", source="test2.txt")
        doc3 = Document(content="other content", source="test3.txt")
        store.add_document(doc1)
        store.add_document(doc2)
        store.add_document(doc3)
        retriever = SimpleRetriever(store)
        result = retriever.retrieve("test", top_k=2)
        assert result.total_retrieved == 2

    def test_retrieve_scoring(self) -> None:
        """Test retrieval scoring."""
        store = DocumentStore()
        doc1 = Document(content="test test test", source="test1.txt")
        doc2 = Document(content="test other", source="test2.txt")
        store.add_document(doc1)
        store.add_document(doc2)
        retriever = SimpleRetriever(store)
        result = retriever.retrieve("test")
        # First doc should have higher score
        assert result.scores[0] >= result.scores[1]


class TestRAG:
    """Tests for RAG class."""

    def test_init(self) -> None:
        """Test RAG initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rag = RAG(checkpoint_dir=tmpdir)
            assert rag.store is not None
            assert rag.retriever is not None
            assert rag.retrieval_count == 0

    def test_add_document(self) -> None:
        """Test adding document to RAG."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rag = RAG(checkpoint_dir=tmpdir)
            doc_id = rag.add_document("Test content", "test.txt")
            assert doc_id
            assert len(rag.get_all_documents()) == 1

    def test_add_document_with_metadata(self) -> None:
        """Test adding document with metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rag = RAG(checkpoint_dir=tmpdir)
            metadata = {"author": "test"}
            doc_id = rag.add_document("Test", "test.txt", metadata)
            doc = rag.store.get_document(doc_id)
            assert doc.metadata == metadata

    def test_retrieve(self) -> None:
        """Test retrieval."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rag = RAG(checkpoint_dir=tmpdir)
            rag.add_document("test content", "test.txt")
            result = rag.retrieve("test")
            assert result.total_retrieved == 1
            assert rag.retrieval_count == 1

    def test_get_augmented_context(self) -> None:
        """Test getting augmented context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rag = RAG(checkpoint_dir=tmpdir)
            rag.add_document("test content", "test.txt")
            context = rag.get_augmented_context("test")
            assert "test content" in context
            assert "Query:" in context

    def test_get_augmented_context_no_query(self) -> None:
        """Test getting augmented context without query."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rag = RAG(checkpoint_dir=tmpdir)
            rag.add_document("test content", "test.txt")
            context = rag.get_augmented_context("test", include_query=False)
            assert "test content" in context
            assert "Query:" not in context

    def test_get_augmented_context_empty(self) -> None:
        """Test getting augmented context with no documents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rag = RAG(checkpoint_dir=tmpdir)
            context = rag.get_augmented_context("test")
            assert "No relevant documents found" in context

    def test_remove_document(self) -> None:
        """Test removing document."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rag = RAG(checkpoint_dir=tmpdir)
            doc_id = rag.add_document("Test", "test.txt")
            removed = rag.remove_document(doc_id)
            assert removed is True
            assert len(rag.get_all_documents()) == 0

    def test_get_documents_by_source(self) -> None:
        """Test getting documents by source."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rag = RAG(checkpoint_dir=tmpdir)
            rag.add_document("Test1", "test.txt")
            rag.add_document("Test2", "test.txt")
            docs = rag.get_documents_by_source("test.txt")
            assert len(docs) == 2

    def test_clear(self) -> None:
        """Test clearing RAG."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rag = RAG(checkpoint_dir=tmpdir)
            rag.add_document("Test", "test.txt")
            rag.clear()
            assert len(rag.get_all_documents()) == 0

    def test_get_status(self) -> None:
        """Test getting RAG status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rag = RAG(checkpoint_dir=tmpdir)
            rag.add_document("Test1", "test1.txt")
            rag.add_document("Test2", "test2.txt")
            rag.retrieve("test")
            status = rag.get_status()
            assert status["total_documents"] == 2
            assert status["total_sources"] == 2
            assert status["retrieval_count"] == 1

    def test_save_checkpoint(self) -> None:
        """Test saving checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rag = RAG(checkpoint_dir=tmpdir)
            rag.add_document("Test", "test.txt")
            checkpoint = rag.save_checkpoint("test_checkpoint")
            assert Path(checkpoint["path"]).exists()
            assert checkpoint["documents_count"] == 1

    def test_load_checkpoint(self) -> None:
        """Test loading checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rag1 = RAG(checkpoint_dir=tmpdir)
            rag1.add_document("Test1", "test1.txt")
            rag1.add_document("Test2", "test2.txt")
            checkpoint = rag1.save_checkpoint("test")

            rag2 = RAG(checkpoint_dir=tmpdir)
            loaded = rag2.load_checkpoint(checkpoint["path"])
            assert loaded["documents_loaded"] == 2
            assert len(rag2.get_all_documents()) == 2

    def test_checkpoint_preserves_metadata(self) -> None:
        """Test that checkpoint preserves document metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rag1 = RAG(checkpoint_dir=tmpdir)
            metadata = {"author": "test", "version": "1.0"}
            rag1.add_document("Test", "test.txt", metadata)
            checkpoint = rag1.save_checkpoint("test")

            rag2 = RAG(checkpoint_dir=tmpdir)
            rag2.load_checkpoint(checkpoint["path"])
            docs = rag2.get_all_documents()
            assert docs[0].metadata == metadata

    def test_multiple_retrievals(self) -> None:
        """Test multiple retrievals increment counter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rag = RAG(checkpoint_dir=tmpdir)
            rag.add_document("Test", "test.txt")
            rag.retrieve("test")
            rag.retrieve("test")
            rag.retrieve("test")
            assert rag.retrieval_count == 3
