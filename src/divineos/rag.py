"""
RAG (Retrieval-Augmented Generation) - Document retrieval and context augmentation.
Manages document storage, embedding, retrieval, and context injection for LLM.
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """Document for RAG system."""

    content: str
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)
    doc_id: str = ""
    created_at: str = ""
    chunk_size: int = 500

    def __post_init__(self) -> None:
        """Validate and initialize document."""
        if not self.content:
            raise ValueError("Document content cannot be empty")
        if not self.source:
            raise ValueError("Document source cannot be empty")

        # Generate doc_id from content hash
        if not self.doc_id:
            content_hash = hashlib.sha256(self.content.encode()).hexdigest()
            self.doc_id = f"{self.source}_{content_hash[:8]}"

        # Set creation timestamp
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def chunk(self) -> list[str]:
        """
        Split document into chunks.

        Returns:
            List of document chunks
        """
        chunks = []
        words = self.content.split()

        current_chunk = []
        current_size = 0

        for word in words:
            word_size = len(word) + 1  # +1 for space
            if current_size + word_size > self.chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_size = word_size
            else:
                current_chunk.append(word)
                current_size += word_size

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def to_dict(self) -> dict[str, Any]:
        """
        Convert document to dictionary.

        Returns:
            Document as dictionary
        """
        return {
            "doc_id": self.doc_id,
            "content": self.content,
            "source": self.source,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


@dataclass
class RetrievalResult:
    """Result from document retrieval."""

    documents: list[Document]
    scores: list[float]
    query: str
    total_retrieved: int

    def get_top_k(self, k: int) -> list[Document]:
        """
        Get top k documents by score.

        Args:
            k: Number of top documents

        Returns:
            Top k documents
        """
        sorted_docs = sorted(
            zip(self.documents, self.scores), key=lambda x: x[1], reverse=True
        )
        return [doc for doc, _ in sorted_docs[:k]]

    def get_context_text(self, k: int = 3, separator: str = "\n---\n") -> str:
        """
        Get context text from top k documents.

        Args:
            k: Number of top documents
            separator: Separator between documents

        Returns:
            Formatted context text
        """
        top_docs = self.get_top_k(k)
        if not top_docs:
            return ""

        context_parts = []
        for doc in top_docs:
            context_parts.append(f"[{doc.source}]\n{doc.content}")

        return separator.join(context_parts)


class DocumentStore:
    """Stores and manages documents for retrieval."""

    def __init__(self) -> None:
        """Initialize document store."""
        self.documents: dict[str, Document] = {}
        self.source_index: dict[str, list[str]] = {}
        logger.info("DocumentStore initialized")

    def add_document(self, document: Document) -> str:
        """
        Add document to store.

        Args:
            document: Document to add

        Returns:
            Document ID
        """
        self.documents[document.doc_id] = document

        # Update source index
        if document.source not in self.source_index:
            self.source_index[document.source] = []
        self.source_index[document.source].append(document.doc_id)

        logger.info(f"Document added: {document.doc_id} from {document.source}")
        return document.doc_id

    def get_document(self, doc_id: str) -> Optional[Document]:
        """
        Get document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Document or None
        """
        return self.documents.get(doc_id)

    def get_documents_by_source(self, source: str) -> list[Document]:
        """
        Get all documents from a source.

        Args:
            source: Document source

        Returns:
            List of documents
        """
        doc_ids = self.source_index.get(source, [])
        return [self.documents[doc_id] for doc_id in doc_ids]

    def remove_document(self, doc_id: str) -> bool:
        """
        Remove document from store.

        Args:
            doc_id: Document ID

        Returns:
            True if removed, False if not found
        """
        if doc_id not in self.documents:
            return False

        doc = self.documents.pop(doc_id)

        # Update source index
        if doc.source in self.source_index:
            self.source_index[doc.source].remove(doc_id)
            if not self.source_index[doc.source]:
                del self.source_index[doc.source]

        logger.info(f"Document removed: {doc_id}")
        return True

    def get_all_documents(self) -> list[Document]:
        """
        Get all documents.

        Returns:
            List of all documents
        """
        return list(self.documents.values())

    def clear(self) -> None:
        """Clear all documents."""
        self.documents.clear()
        self.source_index.clear()
        logger.info("DocumentStore cleared")

    def get_stats(self) -> dict[str, Any]:
        """
        Get store statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "total_documents": len(self.documents),
            "total_sources": len(self.source_index),
            "sources": list(self.source_index.keys()),
        }


class SimpleRetriever:
    """Simple keyword-based document retriever."""

    def __init__(self, store: DocumentStore) -> None:
        """
        Initialize retriever.

        Args:
            store: DocumentStore instance
        """
        self.store = store
        logger.info("SimpleRetriever initialized")

    def retrieve(self, query: str, top_k: int = 5) -> RetrievalResult:
        """
        Retrieve documents matching query.

        Args:
            query: Search query
            top_k: Number of top results

        Returns:
            RetrievalResult with documents and scores
        """
        query_terms = set(query.lower().split())
        documents = self.store.get_all_documents()

        scored_docs = []
        for doc in documents:
            doc_terms = set(doc.content.lower().split())
            # Calculate Jaccard similarity
            intersection = len(query_terms & doc_terms)
            union = len(query_terms | doc_terms)
            score = intersection / union if union > 0 else 0.0
            scored_docs.append((doc, score))

        # Sort by score descending
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        # Extract top k
        top_docs = scored_docs[:top_k]
        result_docs = [doc for doc, _ in top_docs]
        result_scores = [score for _, score in top_docs]

        logger.info(
            f"Retrieved {len(result_docs)} documents for query: {query[:50]}"
        )

        return RetrievalResult(
            documents=result_docs,
            scores=result_scores,
            query=query,
            total_retrieved=len(result_docs),
        )


class RAG:
    """Retrieval-Augmented Generation system."""

    def __init__(self, checkpoint_dir: str = "rag_checkpoints") -> None:
        """
        Initialize RAG system.

        Args:
            checkpoint_dir: Directory for RAG checkpoints
        """
        self.store = DocumentStore()
        self.retriever = SimpleRetriever(self.store)
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)
        self.retrieval_count = 0
        logger.info("RAG system initialized")

    def add_document(
        self, content: str, source: str, metadata: Optional[dict[str, Any]] = None
    ) -> str:
        """
        Add document to RAG system.

        Args:
            content: Document content
            source: Document source
            metadata: Optional metadata

        Returns:
            Document ID
        """
        doc = Document(
            content=content, source=source, metadata=metadata or {}
        )
        doc_id = self.store.add_document(doc)
        logger.info(f"Document added to RAG: {doc_id}")
        return doc_id

    def retrieve(self, query: str, top_k: int = 5) -> RetrievalResult:
        """
        Retrieve documents for query.

        Args:
            query: Search query
            top_k: Number of top results

        Returns:
            RetrievalResult
        """
        self.retrieval_count += 1
        result = self.retriever.retrieve(query, top_k)
        logger.info(f"Retrieval #{self.retrieval_count}: {result.total_retrieved} docs")
        return result

    def get_augmented_context(
        self, query: str, top_k: int = 3, include_query: bool = True
    ) -> str:
        """
        Get augmented context for LLM.

        Args:
            query: Search query
            top_k: Number of top documents
            include_query: Include query in context

        Returns:
            Formatted context string
        """
        result = self.retrieve(query, top_k=top_k)
        context_text = result.get_context_text(k=top_k)

        if not context_text:
            return "No relevant documents found."

        if include_query:
            return f"Query: {query}\n\nRelevant Documents:\n{context_text}"

        return context_text

    def remove_document(self, doc_id: str) -> bool:
        """
        Remove document from RAG.

        Args:
            doc_id: Document ID

        Returns:
            True if removed
        """
        return self.store.remove_document(doc_id)

    def get_documents_by_source(self, source: str) -> list[Document]:
        """
        Get documents by source.

        Args:
            source: Document source

        Returns:
            List of documents
        """
        return self.store.get_documents_by_source(source)

    def get_all_documents(self) -> list[Document]:
        """
        Get all documents.

        Returns:
            List of all documents
        """
        return self.store.get_all_documents()

    def clear(self) -> None:
        """Clear all documents."""
        self.store.clear()
        logger.info("RAG system cleared")

    def get_status(self) -> dict[str, Any]:
        """
        Get RAG status.

        Returns:
            Status dictionary
        """
        store_stats = self.store.get_stats()
        return {
            "total_documents": store_stats["total_documents"],
            "total_sources": store_stats["total_sources"],
            "sources": store_stats["sources"],
            "retrieval_count": self.retrieval_count,
        }

    def save_checkpoint(self, name: Optional[str] = None) -> dict[str, Any]:
        """
        Save RAG checkpoint.

        Args:
            name: Optional checkpoint name

        Returns:
            Checkpoint metadata
        """
        checkpoint_name = name or datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_path = self.checkpoint_dir / f"rag_{checkpoint_name}.json"

        documents_data = [doc.to_dict() for doc in self.store.get_all_documents()]

        checkpoint_data = {
            "timestamp": datetime.now().isoformat(),
            "documents": documents_data,
            "retrieval_count": self.retrieval_count,
        }

        with open(checkpoint_path, "w") as f:
            json.dump(checkpoint_data, f, indent=2)

        logger.info(f"RAG checkpoint saved: {checkpoint_path}")

        return {
            "path": str(checkpoint_path),
            "name": checkpoint_name,
            "timestamp": checkpoint_data["timestamp"],
            "documents_count": len(documents_data),
        }

    def load_checkpoint(self, checkpoint_path: str) -> dict[str, Any]:
        """
        Load RAG checkpoint.

        Args:
            checkpoint_path: Path to checkpoint file

        Returns:
            Loaded checkpoint metadata
        """
        with open(checkpoint_path, "r") as f:
            checkpoint_data = json.load(f)

        self.clear()

        for doc_data in checkpoint_data["documents"]:
            doc = Document(
                content=doc_data["content"],
                source=doc_data["source"],
                metadata=doc_data["metadata"],
                doc_id=doc_data["doc_id"],
                created_at=doc_data["created_at"],
            )
            self.store.add_document(doc)

        self.retrieval_count = checkpoint_data.get("retrieval_count", 0)

        logger.info(
            f"RAG checkpoint loaded: {len(checkpoint_data['documents'])} documents"
        )

        return {
            "path": checkpoint_path,
            "documents_loaded": len(checkpoint_data["documents"]),
            "timestamp": checkpoint_data["timestamp"],
        }
