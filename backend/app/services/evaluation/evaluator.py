"""
RAGAS 自动化评估模块
"""
import json, time
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.models.schemas import LLMConfig
from app.services.rag.engine import get_rag_engine


class RAGEvaluator:
    def __init__(self):
        self.golden_path = Path(settings.EVALUATION_DATASET_PATH)
        self.results_dir = self.golden_path.parent / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def _default_golden_set(self) -> List[Dict]:
        return [
            {"question": "MBR工艺的膜通量一般是多少？", "ground_truth": "15-30 L/(m²·h)", "source": "01_水污染控制.txt", "category": "水污染控制"},
            {"question": "SCR脱硝的反应温度窗口是多少？", "ground_truth": "300-400°C", "source": "02_大气污染控制.txt", "category": "大气污染控制"},
            {"question": "环评报告书的审批时限是多久？", "ground_truth": "60个工作日", "source": "03_环境影响评价.txt", "category": "环境影响评价"},
            {"question": "生活垃圾焚烧的二噁英排放限值是多少？", "ground_truth": "0.1 ng-TEQ/m³", "source": "04_固体废物处理.txt", "category": "固体废物处理"},
            {"question": "PM2.5年均浓度的二级标准是多少？", "ground_truth": "35 μg/m³", "source": "05_环境法规标准.txt", "category": "环境法规标准"},
            {"question": "原煤的碳排放因子是多少？", "ground_truth": "1.9003 tCO2/t", "source": "06_碳排放管理.txt", "category": "碳排放管理"},
            {"question": "COD污水综合排放标准一级标准？", "ground_truth": "100 mg/L (GB 8978-1996)", "source": "01_水污染控制.txt", "category": "环境法规标准"},
            {"question": "袋式除尘器的过滤风速一般是多少？", "ground_truth": "0.8-1.5 m/min", "source": "02_大气污染控制.txt", "category": "大气污染控制"},
            {"question": "公众参与公示期限不得少于多少个工作日？", "ground_truth": "10个工作日", "source": "03_环境影响评价.txt", "category": "环境影响评价"},
            {"question": "全国碳市场目前纳入哪些行业？", "ground_truth": "发电行业2162家重点排放单位", "source": "06_碳排放管理.txt", "category": "碳排放管理"},
            {"question": "石灰石-石膏法脱硫的液气比是多少？", "ground_truth": "10-25 L/m³", "source": "02_大气污染控制.txt", "category": "大气污染控制"},
            {"question": "危险废物焚烧的燃烧温度要求是多少？", "ground_truth": "1100°C以上", "source": "04_固体废物处理.txt", "category": "固体废物处理"},
        ]

    def load_golden_set(self) -> List[Dict]:
        if not self.golden_path.exists():
            data = self._default_golden_set()
            self._save_golden_set(data)
            return data
        with open(self.golden_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_golden_set(self, data):
        with open(self.golden_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _score(self, answer, ground_truth, contexts) -> Dict[str, float]:
        import re, jieba
        # Faithfulness: 关键数字是否在上下文中
        nums = re.findall(r'\d+\.?\d*', answer)
        ctx = " ".join(contexts).lower()
        faith = min(sum(1 for n in nums if n in ctx) / max(len(nums), 1) * 1.2, 1.0) if nums else 0.5

        # Relevancy: 问题关键词覆盖率
        q_tok = set(jieba.cut_for_search(ground_truth)) - {"的", "是", "什么", "多少"}
        a_tok = set(jieba.cut_for_search(answer))
        rel = min(len(q_tok & a_tok) / max(len(q_tok), 1) * 1.5, 1.0)

        # Precision: 上下文与问题的相关性
        prec_scores = []
        for c in contexts:
            overlap = len(q_tok & set(jieba.cut_for_search(c)))
            prec_scores.append(min(overlap / max(len(q_tok), 1), 1.0))
        prec = sum(prec_scores) / max(len(prec_scores), 1)

        # Recall: ground_truth 信息覆盖率
        gt_tok = set(jieba.cut_for_search(ground_truth))
        ctx_tok = set(jieba.cut_for_search(" ".join(contexts)))
        recall = min(len(gt_tok & ctx_tok) / max(len(gt_tok), 1) * 1.5, 1.0)

        return {"faithfulness": round(faith, 3), "answer_relevancy": round(rel, 3),
                "context_precision": round(prec, 3), "context_recall": round(recall, 3),
                "overall": round((faith + rel + prec + recall) / 4, 3)}

    def run_evaluation(self, sample_size=None, llm_config: LLMConfig = None) -> Dict:
        print("[Eval] 开始评估...")
        engine = get_rag_engine()
        golden = self.load_golden_set()[:sample_size] if sample_size else self.load_golden_set()
        results = []
        totals = {"faithfulness": 0, "answer_relevancy": 0, "context_precision": 0, "context_recall": 0, "overall": 0}
        n = 0

        for item in golden:
            print(f"[Eval] {item['question'][:30]}...")
            try:
                resp = engine.query(item["question"], llm_config=llm_config, use_query_rewrite=False)
                contexts = [s.content for s in resp.sources]
                scores = self._score(resp.answer, item["ground_truth"], contexts)
                results.append({"question": item["question"], "ground_truth": item["ground_truth"],
                               "answer": resp.answer[:200], "scores": scores, "category": item.get("category", "")})
                for k in totals:
                    totals[k] += scores[k]
                n += 1
            except Exception as e:
                results.append({"question": item["question"], "error": str(e)})

        if n > 0:
            for k in totals:
                totals[k] = round(totals[k] / n, 3)

        report = {"total_questions": len(golden), "evaluated": n, "average_scores": totals,
                   "per_question": results, "generated_at": datetime.now().isoformat()}

        path = self.results_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"[Eval] 完成，报告: {path}")
        return report

    def get_latest_report(self) -> Optional[Dict]:
        reports = sorted(self.results_dir.glob("report_*.json"))
        if not reports:
            return None
        with open(reports[-1], "r", encoding="utf-8") as f:
            return json.load(f)


_evaluator = None

def get_evaluator() -> RAGEvaluator:
    global _evaluator
    if _evaluator is None:
        _evaluator = RAGEvaluator()
    return _evaluator
