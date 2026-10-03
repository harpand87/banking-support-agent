import hashlib
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class KnowledgeItem:
    source: str
    title: str
    text: str
    topics: tuple[str, ...]
    status: str = "approved"
    effective_date: date | None = None
    review_date: date | None = None
    jurisdiction: str = "US"
    synthetic: bool = True


DEFAULT_CORPUS = Path(__file__).resolve().parents[1] / "data" / "knowledge" / "approved_knowledge.jsonl"
REQUIRED_FIELDS = {
    "source", "title", "text", "topics", "status", "effective_date",
    "review_date", "jurisdiction", "synthetic",
}


def _parse_date(value: Any, field: str, line_number: int) -> date:
    if not isinstance(value, str):
        raise ValueError(f"knowledge line {line_number}: {field} must be an ISO date")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"knowledge line {line_number}: {field} must be an ISO date") from error


def load_knowledge(path: str | Path = DEFAULT_CORPUS) -> tuple[KnowledgeItem, ...]:
    """Load approved synthetic records from a validated UTF-8 JSONL corpus."""
    records: list[KnowledgeItem] = []
    seen_sources: set[str] = set()
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"knowledge line {line_number}: invalid JSON") from error
            if not isinstance(record, dict) or set(record) != REQUIRED_FIELDS:
                raise ValueError(f"knowledge line {line_number}: record fields do not match schema")

            source, title, text, topics = (record[name] for name in ("source", "title", "text", "topics"))
            if not all(isinstance(value, str) and value.strip() for value in (source, title, text)):
                raise ValueError(f"knowledge line {line_number}: source, title, and text must be non-empty strings")
            if not isinstance(topics, list) or not topics or not all(isinstance(topic, str) and topic.strip() for topic in topics):
                raise ValueError(f"knowledge line {line_number}: topics must be a non-empty string list")
            if source in seen_sources:
                raise ValueError(f"knowledge line {line_number}: duplicate source {source}")
            if record["status"] != "approved" or record["synthetic"] is not True:
                raise ValueError(f"knowledge line {line_number}: only approved synthetic records are loadable")
            if not isinstance(record["jurisdiction"], str) or not record["jurisdiction"].strip():
                raise ValueError(f"knowledge line {line_number}: jurisdiction must be a non-empty string")

            effective_date = _parse_date(record["effective_date"], "effective_date", line_number)
            review_date = _parse_date(record["review_date"], "review_date", line_number)
            if review_date < effective_date:
                raise ValueError(f"knowledge line {line_number}: review_date precedes effective_date")
            seen_sources.add(source)
            records.append(KnowledgeItem(
                source, title, text, tuple(topics), record["status"], effective_date,
                review_date, record["jurisdiction"], record["synthetic"],
            ))
    if not records:
        raise ValueError("knowledge corpus contains no records")
    return tuple(records)


KNOWLEDGE = load_knowledge()

STOPWORDS = {
    "what", "how", "the", "for", "and", "does", "not", "that", "this", "with", "from", "may",
    "policy", "policies", "product", "products", "exist", "existing", "to", "is", "of",
}


def search(query: str, limit: int = 3) -> list[KnowledgeItem]:
    if limit <= 0 or not query.strip():
        return []
    terms = set()
    for raw_term in query.split():
        term = raw_term.lower().strip("?!.,:;()[]")
        if term not in STOPWORDS and (len(term) > 2 or term in {"fd", "rd", "sb", "ppf", "kyc", "mf"}):
            terms.add(term)
    scored = []
    for item in KNOWLEDGE:
        haystack = f"{item.title} {item.text} {' '.join(item.topics)}".lower()
        score = sum(term in haystack for term in terms)
        if score:
            scored.append((score, item))
    scored.sort(key=lambda value: value[0], reverse=True)
    if not scored:
        return []
    best_score = scored[0][0]
    return [item for score, item in scored if score == best_score][:limit]


class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class OpenAIEmbeddingProvider:
    """OpenAI-compatible embedding adapter; credentials are read by the SDK from the environment."""

    def __init__(self, model: str = "text-embedding-3-small", client: Any | None = None) -> None:
        if client is None:
            from openai import OpenAI

            client = OpenAI()
        self.client = client
        self.model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(model=self.model, input=texts)
        return [list(item.embedding) for item in response.data]


class ChromaSemanticRetriever:
    """Persistent Chroma vector retrieval with injected semantic embeddings."""

    def __init__(
        self,
        items: tuple[KnowledgeItem, ...] = KNOWLEDGE,
        embeddings: EmbeddingProvider | None = None,
        persist_directory: str | Path = "chroma_db",
        client: Any | None = None,
        max_distance: float = 0.45,
    ) -> None:
        if embeddings is None:
            raise ValueError("an embedding provider is required for semantic retrieval")
        if not 0 <= max_distance <= 2:
            raise ValueError("max_distance must be between 0 and 2")
        if client is None:
            import chromadb

            client = chromadb.PersistentClient(path=str(persist_directory))
        self.items_by_source = {item.source: item for item in items}
        self.embeddings = embeddings
        self.max_distance = max_distance
        corpus_digest = hashlib.sha256("\n".join(item.source + item.text for item in items).encode()).hexdigest()[:12]
        self.collection = client.get_or_create_collection(
            name=f"banking_knowledge_{corpus_digest}", metadata={"hnsw:space": "cosine"},
        )
        if self.collection.count() == 0:
            documents = [item.text for item in items]
            self.collection.add(
                ids=[item.source for item in items],
                embeddings=embeddings.embed(documents),
                documents=documents,
                metadatas=[{"title": item.title} for item in items],
            )

    def search(self, query: str, limit: int = 3) -> list[KnowledgeItem]:
        if limit <= 0 or not query.strip():
            return []
        result = self.collection.query(
            query_embeddings=self.embeddings.embed([query]), n_results=min(limit, len(self.items_by_source)),
        )
        ids = result.get("ids", [[]])[0]
        distances = result.get("distances", [[]])[0]
        return [
            self.items_by_source[source]
            for index, source in enumerate(ids)
            if source in self.items_by_source and (not distances or distances[index] <= self.max_distance)
        ]
