"""
Hybrid Search 混合检索引擎测试
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from langchain_core.documents import Document
from app.services.rag.hybrid_search import HybridSearchEngine


class TestHybridSearchEngineInit:
    def test_initial_state(self):
        engine = HybridSearchEngine()
        assert engine.vector_store is None
        assert engine.bm25 is None
        assert engine.documents == []
        assert engine.tokenized_docs == []


class TestRRFFusion:
    @pytest.fixture
    def engine(self):
        return HybridSearchEngine()

    def test_basic_fusion(self, engine):
        dense = [(0, 0.9), (1, 0.7), (2, 0.5)]
        sparse = [(0, 0.8), (3, 0.6), (1, 0.4)]

        result = engine.rrf_fusion(dense, sparse, k=60)
        # 结果按融合分数降序排列
        assert len(result) > 0
        scores = [s for _, s in result]
        assert scores == sorted(scores, reverse=True)

    def test_doc_in_both_ranks_higher(self, engine):
        """同时出现在 dense 和 sparse 中的文档应有更高的融合分数"""
        dense = [(0, 0.9), (1, 0.5)]
        sparse = [(0, 0.8), (2, 0.5)]

        result = engine.rrf_fusion(dense, sparse)
        # doc 0 在两个列表中都出现，应排第一
        assert result[0][0] == 0

    def test_empty_inputs(self, engine):
        result = engine.rrf_fusion([], [])
        assert result == []

    def test_only_dense(self, engine):
        dense = [(0, 0.9), (1, 0.7)]
        result = engine.rrf_fusion(dense, [])
        assert len(result) == 2
        assert result[0][0] == 0

    def test_only_sparse(self, engine):
        sparse = [(0, 0.8), (1, 0.6)]
        result = engine.rrf_fusion([], sparse)
        assert len(result) == 2

    def test_custom_k(self, engine):
        dense = [(0, 0.9)]
        sparse = [(0, 0.8)]
        r_default = engine.rrf_fusion(dense, sparse, k=60)
        r_custom = engine.rrf_fusion(dense, sparse, k=10)
        # k 越小，排名差异影响越大
        assert r_default[0][1] != r_custom[0][1]

    def test_custom_weights(self, engine):
        # 需要两个文档在不同检索中排名不同才能体现权重差异
        dense = [(0, 0.9), (1, 0.5)]   # doc 0 > doc 1 in dense
        sparse = [(1, 0.8), (0, 0.3)]  # doc 1 > doc 0 in sparse
        r_balanced = engine.rrf_fusion(dense, sparse, w_dense=0.5, w_sparse=0.5)
        r_dense_heavy = engine.rrf_fusion(dense, sparse, w_dense=0.9, w_sparse=0.1)
        # 两者排序可能不同（权重不同导致 doc 0 和 doc 1 的融合分变化）
        assert len(r_balanced) == 2
        assert len(r_dense_heavy) == 2


class TestDenseSearch:
    @pytest.fixture
    def engine(self):
        return HybridSearchEngine()

    def test_no_vector_store(self, engine):
        assert engine.dense_search("test query") == []

    def test_with_results(self, engine, sample_documents):
        engine.documents = sample_documents
        # 直接设置 mock vector_store
        mock_vs = MagicMock()
        mock_vs.similarity_search_with_score.return_value = [
            (sample_documents[0], 0.15),
            (sample_documents[1], 0.25),
        ]
        engine.vector_store = mock_vs

        results = engine.dense_search("MBR 膜通量")
        assert len(results) == 2
        assert all(isinstance(r[0], int) for r in results)
        assert all(isinstance(r[1], float) for r in results)


class TestSparseSearch:
    @pytest.fixture
    def engine(self):
        return HybridSearchEngine()

    def test_no_bm25(self, engine):
        assert engine.sparse_search("test") == []

    def test_with_results(self, engine, sample_documents):
        import jieba
        from rank_bm25 import BM25Okapi

        engine.documents = sample_documents
        engine.tokenized_docs = [list(jieba.cut_for_search(d.page_content)) for d in sample_documents]
        engine.bm25 = BM25Okapi(engine.tokenized_docs)

        results = engine.sparse_search("MBR 膜通量 工艺", top_k=5)
        assert len(results) > 0
        assert all(isinstance(r[0], int) for r in results)
        assert all(isinstance(r[1], float) for r in results)
        # 分数应该都 > 0
        assert all(r[1] > 0 for r in results)


class TestRerank:
    @pytest.fixture
    def engine(self):
        return HybridSearchEngine()

    def test_no_reranker_fallback(self, engine, sample_documents, monkeypatch):
        """没有 reranker 时返回原始 top_k"""
        engine.documents = sample_documents
        engine._reranker = None
        monkeypatch.setattr("app.services.rag.hybrid_search.settings.USE_RERANKER", False)
        result = engine.rerank("test query", [0, 1, 2, 3, 4, 5], top_k=3)
        assert len(result) == 3
        assert [r[0] for r in result] == [0, 1, 2]

    def test_reranker_disabled(self, engine, monkeypatch, sample_documents):
        engine.documents = sample_documents
        monkeypatch.setattr("app.services.rag.hybrid_search.settings.USE_RERANKER", False)
        result = engine.rerank("test", [0, 1, 2], top_k=2)
        assert result[0][1] == 1.0

    def test_out_of_bounds_indices(self, engine, sample_documents):
        """超过文档列表长度的索引应被跳过"""
        engine.documents = sample_documents
        engine._reranker = None
        result = engine.rerank("test", [100, 200], top_k=5)
        assert result == []


class TestSearch:
    @pytest.fixture
    def engine(self):
        return HybridSearchEngine()

    @patch.object(HybridSearchEngine, 'dense_search')
    @patch.object(HybridSearchEngine, 'sparse_search')
    def test_full_pipeline_without_reranker(self, mock_sparse, mock_dense, engine, sample_documents):
        engine.documents = sample_documents
        mock_dense.return_value = [(0, 0.9), (1, 0.7), (2, 0.5)]
        mock_sparse.return_value = [(0, 0.8), (3, 0.6)]

        docs, elapsed = engine.search("MBR 膜通量", top_k=3, use_reranker=False)
        assert len(docs) <= 3
        assert elapsed > 0
        for doc in docs:
            assert isinstance(doc, Document)

    @patch.object(HybridSearchEngine, 'dense_search')
    @patch.object(HybridSearchEngine, 'sparse_search')
    @patch.object(HybridSearchEngine, 'rerank')
    def test_full_pipeline_with_reranker(self, mock_rerank, mock_sparse, mock_dense, engine, sample_documents):
        engine.documents = sample_documents
        mock_dense.return_value = [(0, 0.9), (1, 0.7)]
        mock_sparse.return_value = [(0, 0.8), (2, 0.5)]
        mock_rerank.return_value = [(1, 0.95), (0, 0.8)]

        docs, elapsed = engine.search("test", top_k=2, use_reranker=True)
        assert len(docs) == 2
        # rerank 返回的顺序应为最终顺序
        assert docs[0].page_content == sample_documents[1].page_content


class TestBuildAndLoad:
    @pytest.fixture
    def engine(self):
        return HybridSearchEngine()

    @patch("app.services.rag.hybrid_search.get_embedding_engine")
    def test_build_index(self, mock_get_emb, engine, sample_documents):
        mock_emb_engine = MagicMock()
        mock_emb = MagicMock()
        mock_emb_engine.embeddings = mock_emb
        mock_get_emb.return_value = mock_emb_engine

        with patch("app.services.rag.hybrid_search.FAISS") as mock_faiss:
            engine.build_index(sample_documents)
            assert engine.vector_store is not None
            assert engine.bm25 is not None
            assert len(engine.tokenized_docs) == len(sample_documents)
            mock_faiss.from_documents.assert_called_once()

    @patch("app.services.rag.hybrid_search.get_embedding_engine")
    def test_save_index(self, mock_get_emb, engine, sample_documents, tmp_path):
        mock_emb_engine = MagicMock()
        mock_emb_engine.embeddings = MagicMock()
        mock_get_emb.return_value = mock_emb_engine

        with patch("app.services.rag.hybrid_search.FAISS"):
            engine.build_index(sample_documents)

        save_path = str(tmp_path / "test_index")
        engine.save_index(save_path)

        # 检查 BM25 pickle 文件
        import os
        assert os.path.exists(save_path + "_bm25.pkl")

    @patch("app.services.rag.hybrid_search.get_embedding_engine")
    def test_load_index(self, mock_get_emb, engine, sample_documents, tmp_path):
        mock_emb_engine = MagicMock()
        mock_emb_engine.embeddings = MagicMock()
        mock_get_emb.return_value = mock_emb_engine

        with patch("app.services.rag.hybrid_search.FAISS"):
            engine.build_index(sample_documents)

        save_path = str(tmp_path / "test_index")
        engine.save_index(save_path)

        # 新建 engine 并加载
        engine2 = HybridSearchEngine()
        with patch("app.services.rag.hybrid_search.FAISS") as mock_faiss:
            engine2.load_index(save_path)
            assert engine2.bm25 is not None
