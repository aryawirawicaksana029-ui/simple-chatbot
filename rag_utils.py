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
import re
import uuid

import chromadb
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
import docx

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"  # small, fast, good enough for portfolio-scale RAG
CHUNK_SIZE = 500                # target characters per chunk (soft limit — sentences are never split)
CHUNK_OVERLAP_SENTENCES = 1     # sentence(s) carried into the next chunk, so context isn't lost at the boundary

# ---------- Prompt injection detection ----------
# Heuristic, not foolproof: catches common/obvious injection phrasing in
# uploaded documents (e.g. "ignore previous instructions"). This can't catch
# every creative rephrasing, which is why chatbot_core.py *also* wraps all
# retrieved excerpts in an explicit "this is data, not instructions" frame
# regardless of whether anything gets flagged here — defense in depth, not
# a single point of failure.
INJECTION_PATTERNS = [
    r"ignore (all|any|the)?\s*(previous|prior|above|earlier)\s*instructions",
    r"disregard (all|any|the)?\s*(previous|prior|above|earlier)\s*instructions",
    r"forget (everything|all|your)\s*(instructions|prompt)",
    r"new instructions?:",
    r"system prompt",
    r"you are now",
    r"reveal (your|the) (system prompt|instructions)",
    r"pretend (you are|to be)",
    r"act as (?:if you are|a jailbroken|dan\b)",
    r"jailbreak",
    r"do anything now",
]

_INJECTION_REGEX = re.compile("|".join(INJECTION_PATTERNS), re.IGNORECASE)


def contains_suspected_injection(text: str) -> bool:
    """Heuristic check for common prompt-injection phrasing in a chunk of text."""
    return bool(_INJECTION_REGEX.search(text))


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

def _split_paragraphs(text: str) -> list:
    """Split on blank lines (one or more) between paragraphs."""
    return [p.strip() for p in re.split(r"\n\s*\n+", text) if p.strip()]


def _split_sentences(text: str) -> list:
    """
    Lightweight sentence splitter: breaks after '.', '!', or '?' followed by
    whitespace. This is a heuristic, not real NLP — it can be fooled by
    abbreviations (e.g. "Mr. Smith" reads as two sentences) — but it avoids
    pulling in a full NLP library (nltk/spacy) for what's a fairly small
    accuracy gain in a portfolio RAG pipeline, and it never cuts a sentence
    in half, which is the actual goal here.
    """
    text = text.strip()
    if not text:
        return []
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def chunk_text(text: str, target_size: int = CHUNK_SIZE, overlap_sentences: int = CHUNK_OVERLAP_SENTENCES) -> list:
    """
    Split `text` into chunks that respect sentence (and paragraph) boundaries
    instead of cutting at a fixed character offset mid-word or mid-sentence.

    How it works: the text is split into paragraphs, then into sentences
    within each paragraph, then sentences are greedily packed into a chunk
    until adding the next one would push the chunk past `target_size`
    characters — at which point a new chunk starts, carrying the last
    `overlap_sentences` sentence(s) forward so context isn't lost right at
    the boundary. A single sentence longer than `target_size` (rare, but
    possible — a long run-on clause, for instance) becomes its own chunk
    rather than being cut off mid-word, since respecting sentence boundaries
    takes priority over hitting the exact target size.
    """
    text = text.strip()
    if not text:
        return []

    all_sentences = []
    for paragraph in _split_paragraphs(text):
        all_sentences.extend(_split_sentences(paragraph))

    if not all_sentences:
        return []

    chunks = []
    current = []
    current_length = 0

    for sentence in all_sentences:
        sentence_length = len(sentence) + 1  # +1 accounts for the joining space

        if current and current_length + sentence_length > target_size:
            chunks.append(" ".join(current))
            current = current[-overlap_sentences:] if overlap_sentences else []
            current_length = sum(len(s) + 1 for s in current)

        current.append(sentence)
        current_length += sentence_length

    if current:
        chunks.append(" ".join(current))

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

    def add_document(self, filepath: str) -> dict:
        """
        Reads, chunks, embeds, and stores a document in the knowledge base.
        Each chunk is also scanned for suspected prompt-injection phrasing
        and tagged accordingly in its metadata (used later to warn the user
        and to strengthen the framing when the chunk is retrieved).

        Returns {"chunks": <count>, "flagged": <count of suspicious chunks>}.
        """
        text = load_document_text(filepath)
        chunks = chunk_text(text)

        if not chunks:
            return {"chunks": 0, "flagged": 0}

        filename = os.path.basename(filepath)
        embeddings = self.embedder.encode(chunks).tolist()
        ids = [str(uuid.uuid4()) for _ in chunks]
        flags = [contains_suspected_injection(chunk) for chunk in chunks]
        metadatas = [
            {"source": filename, "chunk_index": i, "injection_flag": flags[i]}
            for i in range(len(chunks))
        ]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )
        return {"chunks": len(chunks), "flagged": sum(flags)}

    def query(self, question: str, top_k: int = 3) -> list:
        """
        Return the top_k most relevant chunks for `question` as a list of
        {"text": ..., "source": ..., "chunk_index": ..., "flagged": bool}
        dicts (empty list if the KB has nothing yet). `source`/`chunk_index`
        let the caller cite exactly which document (and which part of it)
        an answer drew from. `flagged` marks chunks whose source document
        matched suspected prompt-injection phrasing, so the caller can warn
        the model to treat them with extra suspicion.
        """
        if self.collection.count() == 0:
            return []

        query_embedding = self.embedder.encode([question]).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=min(top_k, self.collection.count()),
            include=["documents", "metadatas"],
        )

        if not results["documents"] or not results["documents"][0]:
            return []

        docs = results["documents"][0]
        metas = results["metadatas"][0]
        return [
            {
                "text": doc,
                "source": meta.get("source", "unknown"),
                "chunk_index": meta.get("chunk_index", 0),
                "flagged": bool(meta.get("injection_flag", False)),
            }
            for doc, meta in zip(docs, metas)
        ]

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