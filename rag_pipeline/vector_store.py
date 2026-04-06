import os
import json
import pickle
import logging
import re
import numpy as np
from typing import List, Dict

from sentence_transformers import SentenceTransformer, CrossEncoder
import faiss

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(
        self,
        model_name="all-MiniLM-L6-v2",
        reranker_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
        index_path="data/processed/faiss.index",
        meta_path="data/processed/metadata.pkl",
    ):
        self.model = SentenceTransformer(model_name)
        self.reranker = CrossEncoder(reranker_model)

        self.index_path = index_path
        self.meta_path = meta_path

        self.documents = []
        self.index = None

    # -----------------------------
    # 🔥 BUILD INDEX
    # -----------------------------
    def build(self, documents: List[Dict]):
        self.documents = documents
        texts = [d["content"] for d in documents]

        logger.info(f"Embedding {len(texts)} documents...")

        embeddings = self.model.encode(
            texts,
            batch_size=64,
            show_progress_bar=True,
            normalize_embeddings=True,
        )

        embeddings = np.array(embeddings).astype("float32")

        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embeddings)

        faiss.write_index(self.index, self.index_path)

        with open(self.meta_path, "wb") as f:
            pickle.dump(self.documents, f)

        logger.info(f"Vector store built: {len(documents)} vectors")

    # -----------------------------
    # 🔥 LOAD INDEX
    # -----------------------------
    def load(self):
        if not os.path.exists(self.meta_path):
            return False

        with open(self.meta_path, "rb") as f:
            self.documents = pickle.load(f)

        self.index = faiss.read_index(self.index_path)
        logger.info(f"Vector store loaded: {len(self.documents)} docs")
        return True

    # -----------------------------
    # 🔥 PRODUCT DETECTION
    # -----------------------------
    def extract_products(self, query: str):
        return re.findall(r"[A-Z]{2,}-[A-Z0-9\-]+", query.upper())

    # -----------------------------
    # 🔥 IMPROVED BOOSTING
    # -----------------------------
    def _boost_score(self, doc: Dict, query: str, base_score: float) -> float:
        boosted = base_score

        q = query.lower()
        content = str(doc.get("content", "")).lower()
        product = doc.get("product", "").lower()

        query_products = self.extract_products(query)
        query_products = [p.lower() for p in query_products]

        # ✅ FIXED: softer product penalty (important)
        if query_products:
            if product in query_products:
                boosted += 0.5
            elif product:
                boosted -= 0.1  # 🔥 was -0.5 (too harsh)

        # ✅ dimension/spec boost
        if any(term in q for term in ["dimension", "size", "mm", "weight"]):
            if any(word in content for word in ["dimension", "mm", "cm", "weight", "size"]):
                boosted += 0.3

        # ✅ keyword token boost
        for token in q.split():
            if token in content:
                boosted += 0.02

        return boosted

    # -----------------------------
    # 🔥 SEARCH WITH RERANKING
    # -----------------------------
    def search(self, query: str, top_k: int = 10):
        q_emb = self.model.encode([query], normalize_embeddings=True)
        q_emb = np.array(q_emb).astype("float32")

        # ✅ FIXED: higher recall
        fetch_k = max(top_k * 15, 150)

        scores, indices = self.index.search(q_emb, fetch_k)

        candidates = []

        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.documents):
                doc = self.documents[idx].copy()
                boosted = self._boost_score(doc, query, float(score))
                doc["score"] = boosted
                candidates.append(doc)

        # Take top N for reranking
        candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)[:40]

        # 🔥 Cross-encoder reranking
        pairs = [[query, doc["content"]] for doc in candidates]
        rerank_scores = self.reranker.predict(pairs)

        for doc, r_score in zip(candidates, rerank_scores):
            doc["rerank_score"] = float(r_score)

        final = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)

        return final[:top_k]


# -----------------------------
# 🔥 BUILD FROM JSON
# -----------------------------
def build_vector_store_from_json(docs_path: str):
    with open(docs_path, "r", encoding="utf-8") as f:
        documents = json.load(f)

    store = VectorStore()
    store.build(documents)
    return store