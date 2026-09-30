"""Hybrid retrieval over a tenant's FAQ knowledge base (the entries managed in the dashboard).

- Dense: Gemini embeddings stored on knowledge_base.embedding, searched with pgvector cosine
  distance (plain-Python cosine on SQLite, used by the offline tests).
- Lexical: BM25 over question + answer text, so exact names/emails/terms still match.
- Multi-query: the analyzer rewrites the customer's message into standalone searches; every
  query's dense and lexical rankings are merged with Reciprocal Rank Fusion.
- Near-duplicate answers are dropped so the reply model sees distinct facts.
Entries are (re-)embedded lazily whenever their text changes (sha1 fingerprint).
"""
import hashlib
import logging
import math
import re
import time
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session, undefer

from ..core.config import settings
from ..models.knowledge import KnowledgeEntry
from .embeddings import embed_queries, embed_texts, model_signature

logger = logging.getLogger(__name__)

RRF_K = 60
_STOPWORDS = {
    "a", "an", "the", "is", "are", "am", "was", "be", "to", "of", "in", "on", "for", "and", "or", "it",
    "do", "does", "you", "your", "we", "our", "i", "my", "me", "can", "what", "how", "which", "who",
    "with", "this", "that", "have", "has", "will", "about", "tell", "please",
    "kya", "hai", "hain", "ka", "ki", "ke", "ko", "se", "mein", "aur", "bhi", "aap", "ap", "hum",
}


@dataclass
class KnowledgeHit:
    id: str
    question: str
    answer: str
    dense_score: float = 0.0
    lexical_rank: Optional[int] = None
    rrf: float = 0.0
    dense_available: bool = True   # False when embeddings were unavailable for this search

    @property
    def is_relevant(self) -> bool:
        floor = settings.RAG_MIN_DENSE_SCORE
        if not self.dense_available:
            return self.lexical_rank is not None and self.lexical_rank < 2   # keyword-only degraded mode
        if self.dense_score >= floor:
            return True
        # Strong keyword match (e.g. an exact product/term) with a reasonable semantic score
        return self.lexical_rank is not None and self.lexical_rank < 2 and self.dense_score >= floor - 0.08


def clean_text(value: str) -> str:
    value = (value or "").replace("�", "—")
    return re.sub(r"\s+", " ", value).strip()


def _fingerprint(question: str, answer: str) -> str:
    return hashlib.sha1(f"{model_signature()}\n{question}\n{answer}".encode("utf-8")).hexdigest()


def _doc_text(question: str, answer: str) -> str:
    return f"{question}\n{answer}"


def _tokens(value: str) -> List[str]:
    words = re.findall(r"[\w؀-ۿ@.+-]+", (value or "").lower())
    out = []
    for w in words:
        w = w.strip(".-+")
        if len(w) < 2 or w in _STOPWORDS:
            continue
        if len(w) > 4 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]  # crude plural folding: services -> service
        out.append(w)
    return out


def _is_postgres(db: Session) -> bool:
    return db.get_bind().dialect.name == "postgresql"


CORPUS_TTL_SECONDS = 60  # dashboard edits to the FAQ show up in answers within a minute
_corpus_cache: Dict[str, Tuple[float, list]] = {}


def _load_corpus(db: Session, tenant_id: str, fresh: bool = False):
    """FAQ text for a tenant, cached briefly: the database can be a continent away (~250ms per round trip)."""
    cached = _corpus_cache.get(tenant_id)
    if cached and not fresh and cached[0] > time.time():
        return cached[1]
    rows = db.query(
        KnowledgeEntry.id, KnowledgeEntry.question, KnowledgeEntry.answer, KnowledgeEntry.embedding_hash
    ).filter(KnowledgeEntry.tenant_id == tenant_id, KnowledgeEntry.is_active == True).all()  # noqa: E712
    _corpus_cache[tenant_id] = (time.time() + CORPUS_TTL_SECONDS, rows)
    return rows


async def ensure_embeddings(db: Session, tenant_id: str, corpus=None, limit: Optional[int] = None,
                            patient: bool = False) -> int:
    """Embeds entries that are new or whose text changed. Returns how many were (re-)embedded.
    During a live turn pass a small limit; the startup backfill handles bulk work patiently."""
    corpus = corpus if corpus is not None else _load_corpus(db, tenant_id)
    stale: List[Tuple[str, str, str, str]] = []
    for row in corpus:
        q, a = clean_text(row.question), clean_text(row.answer)
        fp = _fingerprint(q, a)
        if row.embedding_hash != fp:
            stale.append((row.id, q, a, fp))
    if not stale:
        return 0
    stale = stale[:limit] if limit else stale
    try:
        vectors = await embed_texts([_doc_text(q, a) for _, q, a, _ in stale], patient=patient,
                                    timeout=30.0 if patient else 8.0)
    except Exception as e:
        logger.warning("[RAG] embedding %d knowledge entries failed: %s", len(stale), e)
        return 0
    for (entry_id, _, _, fp), vec in zip(stale, vectors):
        db.query(KnowledgeEntry).filter(KnowledgeEntry.id == entry_id).update(
            {"embedding": vec, "embedding_hash": fp}, synchronize_session=False)
    db.commit()
    _corpus_cache.pop(tenant_id, None)
    logger.info("[RAG] embedded %d knowledge entries for tenant %s", len(stale), tenant_id)
    return len(stale)


def _dense_postgres(db: Session, tenant_id: str, vecs: List[List[float]], limit: int) -> List[List[Tuple[str, float]]]:
    """Nearest neighbours for several query vectors in ONE round trip (LATERAL join, HNSW index per query)."""
    literals = ["[" + ",".join(f"{x:.7f}" for x in vec) + "]" for vec in vecs]
    rows = db.execute(text("""
        SELECT q.idx, kb.id, 1 - (kb.embedding <=> q.v) AS score
        FROM (SELECT (ord - 1)::int AS idx, CAST(v AS vector) AS v
              FROM unnest(CAST(:vs AS text[])) WITH ORDINALITY AS t(v, ord)) q
        CROSS JOIN LATERAL (
            SELECT id, embedding FROM knowledge_base
            WHERE tenant_id = :t AND is_active = true AND embedding IS NOT NULL
            ORDER BY embedding <=> q.v
            LIMIT :k
        ) kb
        ORDER BY q.idx, score DESC
    """), {"vs": literals, "t": tenant_id, "k": limit}).fetchall()
    results: List[List[Tuple[str, float]]] = [[] for _ in vecs]
    for idx, doc_id, score in rows:
        results[idx].append((doc_id, float(score)))
    return results


def _dense_python(db: Session, tenant_id: str, vecs: List[List[float]], limit: int) -> List[List[Tuple[str, float]]]:
    rows = db.query(KnowledgeEntry).options(undefer(KnowledgeEntry.embedding)).filter(
        KnowledgeEntry.tenant_id == tenant_id, KnowledgeEntry.is_active == True  # noqa: E712
    ).all()
    results = []
    for vec in vecs:
        scored = [(r.id, float(sum(a * b for a, b in zip(vec, r.embedding))))
                  for r in rows if r.embedding is not None and len(r.embedding)]
        scored.sort(key=lambda x: x[1], reverse=True)
        results.append(scored[:limit])
    return results


def _bm25_rank(query: str, docs: Dict[str, List[str]], limit: int) -> List[str]:
    q_terms = set(_tokens(query))
    if not q_terms or not docs:
        return []
    n = len(docs)
    avgdl = sum(len(t) for t in docs.values()) / n or 1.0
    df = Counter(term for toks in docs.values() for term in set(toks))
    scores = []
    for doc_id, toks in docs.items():
        tf = Counter(toks)
        s = 0.0
        for term in q_terms:
            if term not in tf:
                continue
            idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
            s += idf * tf[term] * 2.2 / (tf[term] + 1.2 * (0.25 + 0.75 * len(toks) / avgdl))
        if s > 0:
            scores.append((doc_id, s))
    scores.sort(key=lambda x: x[1], reverse=True)
    return [d for d, _ in scores[:limit]]


def _near_duplicate(a: str, b: str) -> bool:
    ta, tb = set(_tokens(a)), set(_tokens(b))
    if not ta or not tb:
        return a.strip().lower() == b.strip().lower()
    return len(ta & tb) / len(ta | tb) >= 0.8


async def search(db: Session, tenant_id: str, queries: List[str], k: int = 5) -> List[KnowledgeHit]:
    """Returns up to k distinct hits ordered by fused rank (check .is_relevant before using)."""
    queries = [q.strip() for q in queries if q and q.strip()][:4]
    if not queries:
        return []
    corpus = _load_corpus(db, tenant_id)
    if not corpus:
        return []
    await ensure_embeddings(db, tenant_id, corpus, limit=10)  # a newly added FAQ is searchable right away

    entries = {r.id: (clean_text(r.question), clean_text(r.answer)) for r in corpus}
    docs = {doc_id: _tokens(f"{q} {a}") for doc_id, (q, a) in entries.items()}
    hits: Dict[str, KnowledgeHit] = {}

    def hit(doc_id: str) -> KnowledgeHit:
        if doc_id not in hits:
            q, a = entries[doc_id]
            hits[doc_id] = KnowledgeHit(id=doc_id, question=q, answer=a)
        return hits[doc_id]

    vectors = await embed_queries(queries)
    usable = [v for v in vectors if v is not None]
    dense_ran = False
    if usable:
        dense_fn = _dense_postgres if _is_postgres(db) else _dense_python
        try:
            for ranking in dense_fn(db, tenant_id, usable, 12):
                for rank, (doc_id, score) in enumerate(ranking):
                    if doc_id in entries:
                        h = hit(doc_id)
                        h.dense_score = max(h.dense_score, score)
                        h.rrf += 1.0 / (RRF_K + rank + 1)
            dense_ran = True
        except Exception as e:
            db.rollback()
            logger.warning("[RAG] dense search failed: %s", e)
    for query in queries:
        for rank, doc_id in enumerate(_bm25_rank(query, docs, 12)):
            h = hit(doc_id)
            h.lexical_rank = rank if h.lexical_rank is None else min(h.lexical_rank, rank)
            h.rrf += 1.0 / (RRF_K + rank + 1)

    if not dense_ran:
        for h in hits.values():
            h.dense_available = False
    ranked = sorted(hits.values(), key=lambda h: (h.is_relevant, h.rrf), reverse=True)
    selected: List[KnowledgeHit] = []
    for h in ranked:
        if any(_near_duplicate(h.answer, s.answer) for s in selected):
            continue
        selected.append(h)
        if len(selected) >= k:
            break
    if settings.RAG_DEBUG_LOGGING:
        logger.info("[RAG] %s -> %s", queries,
                    [(h.question[:40], round(h.dense_score, 3), h.lexical_rank) for h in selected])
    return selected


async def backfill_all_tenants() -> None:
    """Startup job: embed every tenant's knowledge, waiting out free-tier rate limits.
    Runs in one worker only (Redis lock) so two workers don't burn the quota twice."""
    from ..core.database import SessionLocal
    from ..core.redis import RedisService
    from ..models.tenant import Tenant

    from ..core.api_keys import get_key
    if not get_key("GEMINI_API_KEY") or not RedisService.acquire_lock("embedding_backfill", ttl_seconds=900):
        return
    db = SessionLocal()
    try:
        for (tenant_id,) in db.query(Tenant.id).all():
            count = await ensure_embeddings(db, tenant_id, _load_corpus(db, tenant_id, fresh=True), patient=True)
            if count:
                logger.warning("[RAG] backfilled %d knowledge embeddings for tenant %s", count, tenant_id)
    except Exception as e:
        logger.warning("[RAG] embedding backfill failed: %s", e)
    finally:
        db.close()
        RedisService.release_lock("embedding_backfill")


_overview_cache: Dict[str, Tuple[float, List[KnowledgeHit]]] = {}


async def company_overview(db: Session, tenant_id: str) -> List[KnowledgeHit]:
    """Background facts about the business (what it is, what it offers), cached for 30 minutes."""
    cached = _overview_cache.get(tenant_id)
    if cached and cached[0] > time.time():
        return cached[1]
    hits = await search(db, tenant_id, ["About the company: who we are and what we do",
                                         "What services, products and packages do we offer?"], k=3)
    hits = [h for h in hits if h.is_relevant]
    _overview_cache[tenant_id] = (time.time() + 1800, hits)
    return hits
