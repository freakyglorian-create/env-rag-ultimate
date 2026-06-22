"""
Hybrid Search 混合检索引擎
Dense(FAISS) + Sparse(BM25) + RRF融合 + Cross-encoder Reranking
"""
import os
import time
import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from rank_bm25 import BM25Okapi
import jieba

from app.core.config import settings
from app.services.embedding.engine import get_embedding_engine


class HybridSearchEngine:
    """
    多阶段检索管道:
    1. Dense Retrieval (FAISS + BGE Embedding)
    2. Sparse Retrieval (BM25 + jieba 中文分词)
    3. RRF Fusion (倒数秩融合)
    4. Cross-encoder Reranking (BGE-Reranker)
    """

    def __init__(self):
        self.vector_store: Optional[FAISS] = None
        self.bm25: Optional[BM25Okapi] = None
        self.documents: List[Document] = []
        self.tokenized_docs: List[List[str]] = []
        self._reranker = None

    def _get_reranker(self):
        if self._reranker is None and settings.USE_RERANKER:
            try:
                from sentence_transformers import CrossEncoder
                self._reranker = CrossEncoder(settings.RERANKER_MODEL)
                print(f"[Reranker] 已加载: {settings.RERANKER_MODEL}")
            except Exception as e:
                print(f"[Reranker] 加载失败: {e}")
        return self._reranker

    def build_index(self, documents: List[Document]):
        print(f"[HybridSearch] 构建索引，文档数: {len(documents)}")
        t0 = time.time()
        self.documents = documents

        # Dense 索引
        print("[HybridSearch] 构建 Dense 索引 (FAISS)...")
        emb = get_embedding_engine()
        self.vector_store = FAISS.from_documents(documents, emb.embeddings)

        # Sparse 索引
        print("[HybridSearch] 构建 Sparse 索引 (BM25 + jieba)...")
        self.tokenized_docs = [list(jieba.cut_for_search(d.page_content)) for d in documents]
        self.bm25 = BM25Okapi(self.tokenized_docs)

        print(f"[HybridSearch] 索引构建完成，耗时: {(time.time()-t0)*1000:.0f}ms")

    def save_index(self, path: str):
        if self.vector_store:
            self.vector_store.save_local(path)
            # 保存 BM25 tokenized docs
            import pickle
            bm25_path = path + "_bm25.pkl"
            with open(bm25_path, "wb") as f:
                pickle.dump((self.tokenized_docs, self.documents), f)

    def load_index(self, path: str):
        emb = get_embedding_engine()
        self.vector_store = FAISS.load_local(path, emb.embeddings, allow_dangerous_deserialization=True)
        # 加载 BM25
        import pickle
        bm25_path = path + "_bm25.pkl"
        if os.path.exists(bm25_path):
            with open(bm25_path, "rb") as f:
                self.tokenized_docs, self.documents = pickle.load(f)
            self.bm25 = BM25Okapi(self.tokenized_docs)
        print(f"[HybridSearch] 索引已加载: {path}")

    def dense_search(self, query: str, top_k: int = 50) -> List[Tuple[int, float]]:
        if not self.vector_store:
            return []
        results = self.vector_store.similarity_search_with_score(query, k=top_k)
        out = []
        for doc, score in results:
            for i, d in enumerate(self.documents):
                if d.page_content == doc.page_content:
                    out.append((i, float(score)))
                    break
        return out

    def sparse_search(self, query: str, top_k: int = 50) -> List[Tuple[int, float]]:
        if not self.bm25:
            return []
        tokens = list(jieba.cut_for_search(query))
        scores = self.bm25.get_scores(tokens)
        top_idx = np.argsort(scores)[::-1][:top_k]
        return [(int(i), float(scores[i])) for i in top_idx if scores[i] > 0]

    def rrf_fusion(self, dense: List[Tuple[int, float]], sparse: List[Tuple[int, float]],
                  k=60, w_dense=0.7, w_sparse=0.3) -> List[Tuple[int, float]]:
        scores = defaultdict(float)
        for rank, (doc_id, _) in enumerate(dense):
            scores[doc_id] += w_dense / (k + rank + 1)
        for rank, (doc_id, _) in enumerate(sparse):
            scores[doc_id] += w_sparse / (k + rank + 1)
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)

    def rerank(self, query: str, doc_indices: List[int], top_k: int = 5) -> List[Tuple[int, float]]:
        reranker = self._get_reranker()
        if not reranker:
            return [(i, 1.0) for i in doc_indices[:top_k]]
        pairs = [[query, self.documents[i].page_content] for i in doc_indices if i < len(self.documents)]
        if not pairs:
            return []
        scores = reranker.predict(pairs)
        scored = sorted(zip(doc_indices[:len(scores)], scores), key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def search(self, query: str, top_k: int = 5, use_reranker: bool = True) -> Tuple[List[Document], float]:
        t0 = time.time()
        dense = self.dense_search(query, top_k=settings.RERANKER_TOP_K)
        sparse = self.sparse_search(query, top_k=settings.RERANKER_TOP_K)
        fused = self.rrf_fusion(dense, sparse, w_dense=settings.DENSE_WEIGHT, w_sparse=settings.BM25_WEIGHT)
        candidates = [idx for idx, _ in fused]

        if use_reranker and settings.USE_RERANKER:
            reranked = self.rerank(query, candidates, top_k=top_k)
            final = [idx for idx, _ in reranked]
        else:
            final = candidates[:top_k]

        results = [self.documents[i] for i in final if i < len(self.documents)]
        return results, (time.time() - t0) * 1000


_hybrid: Optional[HybridSearchEngine] = None

def get_hybrid_search() -> HybridSearchEngine:
    global _hybrid
    if _hybrid is None:
        _hybrid = HybridSearchEngine()
    return _hybrid
