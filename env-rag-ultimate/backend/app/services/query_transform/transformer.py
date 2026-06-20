"""
Query Transform 查询改写模块
- Query Rewriting: LLM 改写为更清晰的检索语句
- Multi-Query: 生成多个查询变体，分别检索后合并
"""
from typing import List, Optional
from app.services.llm.gateway import get_llm_gateway
from app.core.config import settings


QUERY_REWRITE_PROMPT = """你是一个搜索查询优化专家。请将用户的自然语言问题改写为更适合信息检索的查询语句。
要求：
1. 提取核心关键词
2. 补充专业术语的同义词
3. 去除口语化表达
4. 只输出改写后的查询，不要解释

用户问题：{question}
改写查询："""

MULTI_QUERY_PROMPT = """你是一个搜索专家。请为以下问题生成 {n} 个不同角度的查询变体，用于提高检索覆盖率。
每个变体应关注问题的不同方面或使用不同的表述方式。

用户问题：{question}

请输出 {n} 个查询变体，每行一个："""


class QueryTransformer:
    """查询改写器"""

    def __init__(self):
        self.gateway = get_llm_gateway()

    def rewrite_query(self, question: str) -> Optional[str]:
        """单查询改写"""
        if not settings.ENABLE_QUERY_REWRITE:
            return None
        try:
            from langchain.schema import HumanMessage
            llm = self.gateway.get_llm(temperature=0.1)
            resp = llm.invoke([HumanMessage(content=QUERY_REWRITE_PROMPT.format(question=question))])
            rewritten = resp.content.strip() if hasattr(resp, "content") else str(resp).strip()
            return rewritten if rewritten and rewritten != question else None
        except Exception as e:
            print(f"[QueryTransform] 改写失败: {e}")
            return None

    def generate_multi_queries(self, question: str, n: int = 3) -> List[str]:
        """生成多个查询变体"""
        if not settings.ENABLE_MULTI_QUERY:
            return []
        try:
            from langchain.schema import HumanMessage
            llm = self.gateway.get_llm(temperature=0.5)
            resp = llm.invoke([HumanMessage(content=MULTI_QUERY_PROMPT.format(question=question, n=n))])
            text = resp.content.strip() if hasattr(resp, "content") else str(resp).strip()
            queries = [line.strip() for line in text.split("\n") if line.strip()]
            return queries[:n]
        except Exception as e:
            print(f"[QueryTransform] 多查询生成失败: {e}")
            return []


_transformer: Optional[QueryTransformer] = None

def get_query_transformer() -> QueryTransformer:
    global _transformer
    if _transformer is None:
        _transformer = QueryTransformer()
    return _transformer
