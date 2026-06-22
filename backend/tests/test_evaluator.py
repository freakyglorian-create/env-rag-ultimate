"""
RAGAS 评估器测试
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.services.evaluation.evaluator import RAGEvaluator, get_evaluator


class TestRAGEvaluatorInit:
    def test_creates_results_dir(self, tmp_path, monkeypatch):
        eval_dir = tmp_path / "evaluation"
        monkeypatch.setattr("app.services.evaluation.evaluator.settings.EVALUATION_DATASET_PATH",
                           str(eval_dir / "golden_set.json"))
        evaluator = RAGEvaluator()
        assert evaluator.results_dir.exists()

    def test_singleton(self):
        e1 = get_evaluator()
        e2 = get_evaluator()
        assert e1 is e2


class TestGoldenSet:
    def test_default_golden_set(self):
        evaluator = RAGEvaluator()
        data = evaluator._default_golden_set()
        assert len(data) == 12
        for item in data:
            assert "question" in item
            assert "ground_truth" in item
            assert "source" in item
            assert "category" in item

    def test_categories_coverage(self):
        evaluator = RAGEvaluator()
        data = evaluator._default_golden_set()
        categories = {item["category"] for item in data}
        assert "水污染控制" in categories
        assert "大气污染控制" in categories
        assert "环境影响评价" in categories
        assert "固体废物处理" in categories
        assert "环境法规标准" in categories
        assert "碳排放管理" in categories

    def test_mbr_question(self):
        evaluator = RAGEvaluator()
        data = evaluator._default_golden_set()
        q1 = data[0]
        assert "MBR" in q1["question"]
        assert "15-30" in q1["ground_truth"]
        assert q1["source"] == "01_水污染控制.txt"

    def test_save_and_load(self, tmp_path, monkeypatch):
        golden_path = tmp_path / "golden_set.json"
        monkeypatch.setattr("app.services.evaluation.evaluator.settings.EVALUATION_DATASET_PATH",
                           str(golden_path))
        evaluator = RAGEvaluator()
        evaluator.results_dir = tmp_path / "results"
        evaluator.results_dir.mkdir(exist_ok=True)

        data = evaluator.load_golden_set()
        assert len(data) == 12

        # 文件应该被创建
        assert golden_path.exists()
        with open(golden_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        assert len(loaded) == 12


class TestScoring:
    @pytest.fixture
    def evaluator(self):
        return RAGEvaluator()

    def test_perfect_match(self, evaluator):
        answer = "SCR脱硝的反应温度窗口为300-400°C，脱硝效率可达80-95%。"
        ground_truth = "SCR脱硝温度窗口为300-400°C"
        contexts = ["SCR脱硝技术：反应温度窗口为300-400°C，催化剂为V2O5-TiO2基。脱硝效率80-95%。"]

        scores = evaluator._score(answer, ground_truth, contexts)
        assert 0 <= scores["faithfulness"] <= 1.0
        assert 0 <= scores["answer_relevancy"] <= 1.0
        assert 0 <= scores["context_precision"] <= 1.0
        assert 0 <= scores["context_recall"] <= 1.0
        assert 0 <= scores["overall"] <= 1.0

    def test_no_numbers_in_answer(self, evaluator):
        """答案中没有数字时，faithfulness 返回 0.5"""
        answer = "MBR工艺是一种膜生物反应器技术。"
        ground_truth = "15-30 L/(m²·h)"
        contexts = ["MBR膜通量范围：15-30 L/(m²·h)"]

        scores = evaluator._score(answer, ground_truth, contexts)
        assert scores["faithfulness"] == 0.5  # no nums -> default

    def test_relevancy_with_overlap(self, evaluator):
        answer = "污水处理COD排放标准为100 mg/L (GB 8978-1996)"
        ground_truth = "COD排放标准 100 mg/L"
        contexts = ["COD一级标准100 mg/L"]

        scores = evaluator._score(answer, ground_truth, contexts)
        assert scores["answer_relevancy"] > 0.3  # keywords overlap

    def test_all_dims_in_range(self, evaluator):
        """验证所有评分维度都在 [0, 1] 范围内"""
        answer = "原煤碳排放因子约为1.9 tCO2/t"
        ground_truth = "原煤碳排放因子1.9003 tCO2/t"
        contexts = ["原煤的碳排放因子为1.9003 tCO2/t，是所有化石能源中最高的之一。"]

        scores = evaluator._score(answer, ground_truth, contexts)
        for key in ["faithfulness", "answer_relevancy", "context_precision", "context_recall", "overall"]:
            assert 0 <= scores[key] <= 1.0, f"{key} = {scores[key]} out of range"


class TestRunEvaluation:
    @pytest.fixture
    def evaluator(self, tmp_path, monkeypatch):
        eval_dir = tmp_path / "evaluation"
        eval_dir.mkdir(exist_ok=True)
        monkeypatch.setattr("app.services.evaluation.evaluator.settings.EVALUATION_DATASET_PATH",
                           str(eval_dir / "golden_set.json"))
        evaluator = RAGEvaluator()
        evaluator.results_dir = eval_dir / "results"
        evaluator.results_dir.mkdir(exist_ok=True)
        return evaluator

    @patch("app.services.evaluation.evaluator.get_rag_engine")
    def test_sample_size_limit(self, mock_get_engine, evaluator, golden_set):
        """sample_size 应限制评估的问题数"""
        # 替换 golden set
        evaluator._default_golden_set = MagicMock(return_value=golden_set)
        evaluator._save_golden_set = MagicMock()

        mock_engine = MagicMock()
        mock_resp = MagicMock()
        mock_resp.answer = "MBR膜通量一般为15-30 L/(m²·h)"
        mock_resp.sources = [MagicMock(content="MBR膜通量15-30")]
        mock_engine.query.return_value = mock_resp
        mock_get_engine.return_value = mock_engine

        cfg = MagicMock()
        report = evaluator.run_evaluation(sample_size=1, llm_config=cfg)
        assert report["evaluated"] == 1

    @patch("app.services.evaluation.evaluator.get_rag_engine")
    def test_error_handling(self, mock_get_engine, evaluator, golden_set):
        """单个问题出错不应中断整个评估"""
        evaluator._default_golden_set = MagicMock(return_value=golden_set)
        evaluator._save_golden_set = MagicMock()

        mock_engine = MagicMock()
        # 第一个成功，第二个抛异常
        mock_resp = MagicMock()
        mock_resp.answer = "test answer"
        mock_resp.sources = [MagicMock(content="test context")]
        mock_engine.query.side_effect = [mock_resp, Exception("LLM error")]

        mock_get_engine.return_value = mock_engine

        cfg = MagicMock()
        report = evaluator.run_evaluation(sample_size=2, llm_config=cfg)
        assert report["evaluated"] == 1
        assert any("error" in item for item in report["per_question"])


class TestGetLatestReport:
    def test_no_reports(self, tmp_path):
        evaluator = RAGEvaluator()
        evaluator.results_dir = tmp_path / "empty_results"
        evaluator.results_dir.mkdir(exist_ok=True)
        assert evaluator.get_latest_report() is None

    def test_returns_latest(self, tmp_path):
        evaluator = RAGEvaluator()
        evaluator.results_dir = tmp_path
        (tmp_path / "report_20240101_000000.json").write_text(
            json.dumps({"timestamp": "old"}), encoding="utf-8"
        )
        (tmp_path / "report_20240102_000000.json").write_text(
            json.dumps({"timestamp": "new"}), encoding="utf-8"
        )
        report = evaluator.get_latest_report()
        assert report["timestamp"] == "new"
