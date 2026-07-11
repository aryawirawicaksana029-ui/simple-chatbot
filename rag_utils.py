"""
rag_utils.py
Lightweight RAG (Retrieval-Augmented Generation) knowledge base, built on
ChromaDB (vector storage) + sentence-transformers (local embeddings).
Shared by the CLI, GUI, and Web App versions of ARIA.

Design note: the knowledge base is a single, shared store persisted to
disk — it represents documents Aria "knows about" globally, separate
from any one chat's conversation history (which stays in-memory per
AriaChatbot instance / per browser session).

Why sentence-transformers instead of Groq for embeddings: Groq's API
currently only hosts chat, Whisper (speech-to-text), and TTS models —
no embedding endpoint. sentence-transformers runs locally, is free, and
needs no extra API key, at the cost of a one-time ~80MB model download
and a slightly slower first run.
"""

import os
import uuid

import chromadb
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
import docx

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"  # small, fast, good enough for portfolio-scale RAG
CHUNK_SIZE = 500     # characters per chunk
CHUNK_OVERLAP = 50   # overlap between consecutive chunks, so context isn't cut mid-thought


# ---------- Document loaders ----------

def _read_txt(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _read_pdf(filepath: str) -> str:
    reader = PdfReader(filepath)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _read_docx(filepath: str) -> str:
    document = docx.Document(filepath)
    return "\n".join(p.text for p in document.paragraphs)


def load_document_text(filepath: str) -> str:
    """Extract raw text from a .txt, .pdf, or .docx file."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".txt":
        return _read_txt(filepath)
    elif ext == ".pdf":
        return _read_pdf(filepath)
    elif ext == ".docx":
        return _read_docx(filepath)
    else:
        raise ValueError(f"Unsupported file type: {ext} (only .txt, .pdf, .docx are supported)")


# ---------- Chunking ----------

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list:
    """
    Simple fixed-size character chunking with overlap. Good enough for a
    portfolio RAG pipeline — production systems usually chunk by sentence
    or paragraph boundaries instead, but this keeps the logic easy to
    reason about (and explain in an interview).
    """
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


# ---------- Knowledge base ----------

class KnowledgeBase:
    """Wraps a persistent ChromaDB collection + a local embedding model."""

    def __init__(self, persist_directory: str = "knowledge_base"):
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)

        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(name="aria_documents")

        # Loaded once per process — this is the slow part on first run
        # (downloads ~80MB of model weights, then caches them locally).
        self.embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)

    def add_document(self, filepath: str) -> int:
        """
        Reads, chunks, embeds, and stores a document in the knowledge base.
        Returns the number of chunks that were added (0 if the file had no
        extractable text).
        """
        text = load_document_text(filepath)
        chunks = chunk_text(text)

        if not chunks:
            return 0

        filename = os.path.basename(filepath)
        embeddings = self.embedder.encode(chunks).tolist()
        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [{"source": filename, "chunk_index": i} for i in range(len(chunks))]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )
        return len(chunks)

    def query(self, question: str, top_k: int = 3) -> list:
        """Return the top_k most relevant chunks for `question` (empty list if the KB has nothing yet)."""
        if self.collection.count() == 0:
            return []

        query_embedding = self.embedder.encode([question]).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=min(top_k, self.collection.count()),
        )
        return results["documents"][0] if results["documents"] else []

    def list_documents(self) -> list:
        """Return the unique source filenames currently stored in the knowledge base."""
        if self.collection.count() == 0:
            return []
        data = self.collection.get(include=["metadatas"])
        sources = {meta["source"] for meta in data["metadatas"]}
        return sorted(sources)

    def clear(self):
        """Wipe the entire knowledge base — all documents, all chunks."""
        self.client.delete_collection("aria_documents")
        self.collection = self.client.get_or_create_collection(name="aria_documents")
