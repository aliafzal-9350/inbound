import os
import re
import json
import math
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from collections import Counter
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..core.config import settings
from ..models.knowledge import TenantKnowledgeChunk, KnowledgeEntry

logger = logging.getLogger(__name__)


class LocalSemanticVectorizer:
    """Fast, dependency-free character and sub-word n-gram vectorizer for dense-like semantic similarity."""
    
    @staticmethod
    def _tokenize(text_str: str) -> List[str]:
        cleaned = re.sub(r"[^\w\s\u0600-\u06FF]", " ", text_str.lower())
        words = [w for w in cleaned.split() if len(w) > 1]
        tokens = list(words)
        for w in words:
            if len(w) >= 3:
                # Add character 3-grams and 4-grams for subword matching
                for i in range(len(w) - 2):
                    tokens.append(w[i:i+3])
                for i in range(len(w) - 3):
                    tokens.append(w[i:i+4])
        return tokens

    @classmethod
    def compute_similarity(cls, text1: str, text2: str) -> float:
        if not text1 or not text2:
            return 0.0
        
        tokens1 = cls._tokenize(text1)
        tokens2 = cls._tokenize(text2)
        if not tokens1 or not tokens2:
            return 0.0

        vec1 = Counter(tokens1)
        vec2 = Counter(tokens2)

        intersection = set(vec1.keys()) & set(vec2.keys())
        numerator = sum([vec1[x] * vec2[x] for x in intersection])

        sum1 = sum([vec1[x] ** 2 for x in vec1.keys()])
        sum2 = sum([vec2[x] ** 2 for x in vec2.keys()])
        denominator = math.sqrt(sum1) * math.sqrt(sum2)

        if not denominator:
            return 0.0
        return float(numerator) / denominator


class EmbeddingService:
    """Generates embedding vectors via Ollama, OpenAI, Gemini, or local vectorizer."""
    _ollama_has_embed_model: Optional[bool] = None

    @classmethod
    def get_embedding(cls, query_text: str) -> Optional[List[float]]:
        if not query_text or not query_text.strip():
            return None

        # 1. Try Ollama embeddings only if an embedding model is confirmed available
        if cls._ollama_has_embed_model is not False:
            try:
                import httpx
                base_url = (settings.OLLAMA_BASE_URL or "http://localhost:11434").rstrip("/")
                resp = httpx.post(
                    f"{base_url}/api/embeddings",
                    json={"model": "nomic-embed-text", "prompt": query_text},
                    timeout=1.0
                )
                if resp.status_code == 200:
                    cls._ollama_has_embed_model = True
                    emb = resp.json().get("embedding")
                    if emb and isinstance(emb, list):
                        return emb
                else:
                    cls._ollama_has_embed_model = False
            except Exception:
                cls._ollama_has_embed_model = False

        # 2. Try OpenAI embeddings
        if settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY) > 10 and not settings.OPENAI_API_KEY.startswith("AQ."):
            try:
                import openai
                client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                resp = client.embeddings.create(
                    model="text-embedding-3-small",
                    input=query_text
                )
                return resp.data[0].embedding
            except Exception as e:
                logger.debug(f"OpenAI embedding generation skipped: {e}")

        # 3. Try Gemini embeddings
        if settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY) > 10 and not settings.GEMINI_API_KEY.startswith("AQ."):
            try:
                from google import genai
                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                resp = client.models.embed_content(
                    model="text-embedding-004",
                    contents=query_text
                )
                emb = resp.embedding.values
                if len(emb) == 768:
                    emb = list(emb) + [0.0] * (1536 - 768)
                return emb[:1536]
            except Exception as e:
                logger.debug(f"Gemini embedding generation skipped: {e}")

        return None


async def get_embedding(query_text: str) -> Optional[List[float]]:
    return EmbeddingService.get_embedding(query_text)


class HybridRAGEngine:
    RRF_K: int = 60

    SEMANTIC_SYNONYM_MAP: Dict[str, List[str]] = {
        "developer": ["developer", "developers", "development", "dev", "devs", "engineer", "engineers", "engineering", "technical team", "tech team", "coder", "programmer", "software engineer", "software developers", "ai developers"],
        "developers": ["developer", "developers", "development", "dev", "devs", "engineer", "engineers", "engineering", "technical team", "tech team", "coder", "programmer", "software engineer", "software developers", "ai developers"],
        "development": ["developer", "developers", "development", "dev", "devs", "engineer", "engineers", "engineering", "technical team", "tech team", "software"],
        "engineer": ["developer", "developers", "development", "engineer", "engineers", "engineering", "technical team", "software"],
        "engineers": ["developer", "developers", "development", "engineer", "engineers", "engineering", "technical team", "software"],
        "engineering": ["developer", "developers", "development", "engineer", "engineers", "engineering", "technical team", "software"],
        "technical": ["technical", "tech team", "technical team", "engineering team", "developers", "development team"],
        "programmer": ["developer", "developers", "software engineer", "coder", "development team"],
        "timing": ["timing", "timings", "hours", "open", "close", "schedule", "time", "subah", "raat", "khule", "band"],
        "timings": ["timing", "timings", "hours", "open", "close", "schedule", "time", "subah", "raat", "khule", "band"],
        "hours": ["timing", "timings", "hours", "open", "close", "schedule", "time"],
        "price": ["price", "rate", "cost", "fee", "charges", "kitne", "kitna", "pkr", "rates", "pricing", "quote", "consultation", "packages", "plans"],
        "pricing": ["price", "rate", "cost", "fee", "charges", "kitne", "kitna", "pkr", "rates", "pricing", "quote", "consultation", "packages", "plans"],
        "cost": ["price", "rate", "cost", "fee", "charges", "kitne", "kitna", "pkr", "rates", "pricing", "quote", "consultation", "packages", "plans"],
        "rates": ["price", "rate", "cost", "fee", "charges", "kitne", "kitna", "pkr", "rates", "pricing", "quote", "consultation"],
        "service": ["service", "services", "automation", "chatbot", "chatbots", "voice", "agents", "whatsapp", "crm", "workflow", "custom", "solutions"],
        "services": ["service", "services", "automation", "chatbot", "chatbots", "voice", "agents", "whatsapp", "crm", "workflow", "custom", "solutions"],
        "estate": ["real estate", "property", "industries", "leads", "lead qualification", "whatsapp automation"],
        "real": ["real estate", "property", "industries", "leads", "lead qualification", "whatsapp automation"],
        "hvac": ["hvac", "home services", "industries", "calls", "voice agents", "emergency calls"],
        "clinic": ["aesthetics", "clinics", "healthcare", "appointments", "doctor", "medical"],
        "doctor": ["aesthetics", "clinics", "healthcare", "appointments", "doctor", "medical"],
        "ecommerce": ["e-commerce", "retail", "orders", "support", "products", "online store"],
        "packages": ["basic", "all-in-one", "premium", "packages", "plans", "solutions", "package"],
        "package": ["basic", "all-in-one", "premium", "packages", "plans", "solutions", "package"],
        "consultation": ["free consultation", "free offer", "strategy", "book call", "quote", "demo"],
        "demo": ["demo", "consultation", "free consultation", "call", "meeting", "book demo"],
        "ceo": ["ceo", "founder", "owner", "boss", "director", "leadership", "usama anis"],
        "founder": ["ceo", "founder", "owner", "boss", "director", "leadership", "usama anis"],
        "office": ["office", "location", "address", "located", "kahan", "lahore", "casper", "mcleod"],
        "located": ["office", "location", "address", "located", "kahan", "lahore", "casper", "mcleod"],
        "location": ["office", "location", "address", "located", "kahan", "lahore", "casper", "mcleod"],
        "contact": ["contact", "email", "phone", "number", "whatsapp", "reach", "call", "rabta"],
        "email": ["email", "mail", "gmail", "e-mail", "contact"],
        "phone": ["phone", "number", "whatsapp", "call", "contact", "rabta"],
        "team": ["team", "teams", "staff", "employees", "members", "developers", "engineers"],
        "employees": ["team", "staff", "employees", "members", "size", "count", "developers"],
    }

    @classmethod
    def expand_query(cls, query: str) -> Set[str]:
        """Expands query terms with semantically related synonyms and technical concepts."""
        stopwords = {"kya", "hai", "hain", "ko", "ki", "ka", "ke", "aur", "mein", "se", "par", "the", "is", "at", "which", "on", "a", "an", "for", "to", "in", "bhi", "bhai", "aap", "ap", "do", "you", "have", "how", "many", "what", "tell", "me", "about"}
        words = [w.lower().strip(",.?!:;\"'") for w in query.split() if w.lower() not in stopwords and len(w) > 1]
        expanded = set(words)
        for w in words:
            if w in cls.SEMANTIC_SYNONYM_MAP:
                expanded.update(cls.SEMANTIC_SYNONYM_MAP[w])
        return expanded

    @classmethod
    def search(
        cls,
        db: Session,
        tenant_id: str,
        query: str,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, Any]]:
        """Executes Hybrid Semantic Search (Dense Vector + Semantic Trigram / N-gram Similarity) with RRF."""
        if not query or not query.strip():
            return []

        k = top_k or getattr(settings, "RAG_TOP_K", 4)
        threshold = similarity_threshold or getattr(settings, "RAG_SIMILARITY_THRESHOLD", 0.25)
        debug_enabled = getattr(settings, "RAG_DEBUG_LOGGING", True)

        if debug_enabled:
            logger.info(f"[RAG SEARCH] Starting search for query: '{query}' (tenant_id={tenant_id}, top_k={k}, threshold={threshold})")

        expanded_terms = cls.expand_query(query)

        # Contextual retrieval: resolve pronouns and follow-up references using recent history
        pronouns = {"they", "them", "it", "their", "theirs", "those", "these", "he", "she", "him", "her", "yeh", "ye", "woh", "wo", "unka", "unkay", "iski", "iska", "experienced", "experience"}
        query_words_set = set(w.lower().strip(",.?!:;\"'") for w in query.split())
        has_pronoun = bool(query_words_set.intersection(pronouns))
        if has_pronoun and conversation_history:
            recent_context_words = []
            for msg in conversation_history[-3:]:
                content = msg.get("content", "")
                recent_context_words.extend([w.lower().strip(",.?!:;\"'") for w in content.split() if len(w) > 2])
            for w in recent_context_words:
                if w in cls.SEMANTIC_SYNONYM_MAP:
                    expanded_terms.update(cls.SEMANTIC_SYNONYM_MAP[w])
                expanded_terms.add(w)

        expanded_query_text = query + " " + " ".join(expanded_terms)

        dense_ranked_ids: List[str] = []
        sparse_ranked_ids: List[str] = []
        chunks_by_id: Dict[str, Dict[str, Any]] = {}

        # 1. Fetch Candidate Knowledge Entries (from tenant_knowledge_chunks & knowledge_base)
        all_candidates: List[Dict[str, Any]] = []

        try:
            # A. TenantKnowledgeChunk
            chunks = db.query(TenantKnowledgeChunk).filter(
                (TenantKnowledgeChunk.tenant_id == tenant_id) | (TenantKnowledgeChunk.tenant_id == "default")
            ).all()
            for c in chunks:
                c_id = f"chunk_{c.id}"
                c_full = f"{c.chunk_title or ''} {c.chunk_content} {c.category or ''}".strip()
                all_candidates.append({
                    "id": c_id,
                    "category": c.category or "general",
                    "title": c.chunk_title or "Company Knowledge",
                    "content": c.chunk_content,
                    "full_text": c_full,
                    "embedding": getattr(c, "embedding", None),
                })
        except Exception as e:
            logger.debug(f"[RAG] Error querying TenantKnowledgeChunk: {e}")

        try:
            # B. KnowledgeEntry
            entries = db.query(KnowledgeEntry).filter(
                (KnowledgeEntry.tenant_id == tenant_id) | (KnowledgeEntry.tenant_id == "default"),
                KnowledgeEntry.is_active == True
            ).all()
            for e in entries:
                e_id = f"entry_{e.id}"
                e_full = f"Q: {e.question}\nA: {e.answer}".strip()
                all_candidates.append({
                    "id": e_id,
                    "category": "FAQ",
                    "title": e.question,
                    "content": e_full,
                    "full_text": f"{e.question} {e.answer}",
                    "embedding": None,
                })
        except Exception as e:
            logger.debug(f"[RAG] Error querying KnowledgeEntry: {e}")

        # C. Include Curated Brand Facts (RAVISN dataset) as knowledge chunks
        try:
            from .ravisn_knowledge_base import RAVISN_QA_DATA
            for idx, item in enumerate(RAVISN_QA_DATA):
                b_id = f"brand_{idx}"
                b_content = f"Q: {item['q']}\nA: {item['a']}"
                all_candidates.append({
                    "id": b_id,
                    "category": item.get("cat", "brand"),
                    "title": item["q"],
                    "content": b_content,
                    "full_text": f"{item['q']} {item['a']}",
                    "embedding": None,
                })
        except Exception as e:
            logger.debug(f"[RAG] Error loading brand dataset: {e}")

        # 2. Semantic & Lexical Scoring for Candidates
        scored_candidates: List[Tuple[float, Dict[str, Any]]] = []
        for cand in all_candidates:
            # Calculate semantic similarity
            sim1 = LocalSemanticVectorizer.compute_similarity(query, cand["full_text"])
            sim2 = LocalSemanticVectorizer.compute_similarity(expanded_query_text, cand["full_text"])
            
            # Word overlap with query and expanded terms
            cand_words = set(cand["full_text"].lower().split())
            word_overlap = len(expanded_terms.intersection(cand_words))
            overlap_bonus = min(0.35, word_overlap * 0.10)

            total_sim = max(sim1, sim2 * 0.85) + overlap_bonus
            if total_sim >= threshold:
                scored_candidates.append((total_sim, cand))

        # Sort sparse/semantic candidates by score
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        for score, cand in scored_candidates[:15]:
            c_id = cand["id"]
            sparse_ranked_ids.append(c_id)
            chunks_by_id[c_id] = {
                "id": c_id,
                "category": cand["category"],
                "title": cand["title"],
                "content": cand["content"],
                "similarity_score": round(score, 4),
            }

        # 3. Dense Vector Search (pgvector if database supports it and embedding exists)
        embedding = EmbeddingService.get_embedding(query)
        if embedding:
            try:
                dense_sql = text("""
                    SELECT id, category, chunk_title, chunk_content,
                           1 - (embedding <=> :emb::vector) AS cosine_similarity
                    FROM tenant_knowledge_chunks
                    WHERE (tenant_id = :tenant_id OR tenant_id = 'default')
                          AND embedding IS NOT NULL
                          AND (1 - (embedding <=> :emb::vector)) >= :threshold
                    ORDER BY embedding <=> :emb::vector
                    LIMIT 10
                """)
                emb_str = f"[{','.join(str(x) for x in embedding)}]"
                dense_rows = db.execute(
                    dense_sql,
                    {"tenant_id": tenant_id, "emb": emb_str, "threshold": threshold}
                ).fetchall()
                for r in dense_rows:
                    c_id = f"chunk_{r[0]}"
                    dense_ranked_ids.append(c_id)
                    chunks_by_id[c_id] = {
                        "id": c_id,
                        "category": r[1] or "general",
                        "title": r[2] or "Company Knowledge",
                        "content": r[3],
                        "similarity_score": round(float(r[4]), 4)
                    }
            except Exception as e:
                logger.debug(f"pgvector dense search skipped: {e}")

        # 4. Reciprocal Rank Fusion (RRF)
        if not dense_ranked_ids and not sparse_ranked_ids:
            if debug_enabled:
                logger.info(f"[RAG SEARCH] No chunks met threshold {threshold} for query '{query}'")
            return []

        rrf_scores: Dict[str, float] = {}
        for rank, c_id in enumerate(dense_ranked_ids):
            rrf_scores[c_id] = rrf_scores.get(c_id, 0.0) + (1.0 / (cls.RRF_K + rank + 1))

        for rank, c_id in enumerate(sparse_ranked_ids):
            rrf_scores[c_id] = rrf_scores.get(c_id, 0.0) + (1.0 / (cls.RRF_K + rank + 1))

        sorted_chunks = sorted(rrf_scores.items(), key=lambda item: item[1], reverse=True)

        results = []
        max_chunks = getattr(settings, "RAG_MAX_CONTEXT_CHUNKS", 5)
        effective_limit = min(k, max_chunks)

        for c_id, rrf_score in sorted_chunks[:effective_limit]:
            if c_id in chunks_by_id:
                chunk = chunks_by_id[c_id]
                chunk["rrf_score"] = round(rrf_score, 5)
                results.append(chunk)

        if debug_enabled:
            logger.info(f"[RAG SEARCH] Retrieved {len(results)} chunks for query '{query}':")
            for idx, ch in enumerate(results, 1):
                logger.info(f"   [{idx}] Title: {ch['title']} | Score: {ch.get('similarity_score')} | RRF: {ch.get('rrf_score')}")

        return results

    @classmethod
    def build_evidence_pack(cls, chunks: List[Dict[str, Any]]) -> str:
        """Wraps retrieved chunks with metadata into an organized Knowledge Evidence Pack for LLM."""
        if not chunks:
            return ""

        pack_lines = []
        for i, c in enumerate(chunks, start=1):
            category = c.get("category", "General")
            title = c.get("title", f"Document #{i}")
            content = c.get("content", "").strip()
            pack_lines.append(f"[SOURCE {i}] ({category}) {title}\n{content}")

        return "\n\n".join(pack_lines)


def retrieve_knowledge_facts_sync(
    db: Session,
    tenant_id: str,
    query: str,
    top_k: int = 4,
    similarity_threshold: Optional[float] = None
) -> str:
    """Synchronous dynamic KB retrieval fetching relevant facts for a tenant."""
    greetings = {"hi", "hello", "salam", "asslamualikom", "assalamualaykum", "aoa", "hey"}
    clean_query = (query or "").strip().lower()
    if clean_query in greetings:
        return "NO_KB_REQUIRED_GREETING"

    chunks = HybridRAGEngine.search(
        db=db,
        tenant_id=tenant_id,
        query=query,
        top_k=top_k,
        similarity_threshold=similarity_threshold
    )
    if not chunks:
        return "No specific company knowledge found in database matching this inquiry."

    return HybridRAGEngine.build_evidence_pack(chunks)


async def retrieve_knowledge_facts(
    tenant_id: str,
    query: str,
    db: Optional[Session] = None,
    top_k: int = 4,
    similarity_threshold: Optional[float] = None
) -> str:
    """Async dynamic KB retrieval connecting PostgreSQL / SQLite knowledge base to prompt context."""
    from ..core.database import SessionLocal
    local_db = db or SessionLocal()
    try:
        return retrieve_knowledge_facts_sync(local_db, tenant_id, query, top_k, similarity_threshold)
    finally:
        if db is None:
            local_db.close()
