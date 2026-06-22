"""
RAG 核心引擎 - 整合所有模块
Hybrid Search + Query Transform + LLM Factory + 环境工程 Prompt
"""
import time, json
from typing import List, Dict, Optional, Iterator
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate

from app.core.config import settings
from app.models.schemas import QueryResponse, SourceDocument, LLMConfig
from app.services.rag.hybrid_search import get_hybrid_search
from app.services.llm.factory import LLMFactory, PROVIDER_CATALOG
from app.services.query_transform.transformer import get_query_transformer
from app.services.parser.document_parser import DocumentParser

ENV_PROMPT = """你是资深环境工程专家，拥有环保法规、污染治理技术和环境影响评价的丰富经验。

请基于以下参考资料回答问题。若资料不足，请明确说明。

=== 参考资料 ===
{context}
=== 参考资料结束 ===

问题：{question}

要求：
1. 专业准确，符合环境工程规范
2. 涉及标准请注明编号和限值（如 GB 8978-1996）
3. 涉及技术方案应说明适用条件和优缺点
4. 涉及法规应引用具体名称和条款
5. 末尾列出参考资料来源

回答："""


class RAGEngine:
    def __init__(self):
        self.search = get_hybrid_search()
        self.transformer = get_query_transformer()
        self.prompt = PromptTemplate(template=ENV_PROMPT, input_variables=["context", "question"])
        self._ready = False

    def build_knowledge_base(self, directory: str) -> Dict:
        t0 = time.time()
        raw = DocumentParser.parse_directory(directory)
        if not raw:
            raise ValueError("未找到文档")
        chunks = DocumentParser.split_documents(raw)
        self.search.build_index(chunks)
        self.search.save_index(str(settings.VECTOR_STORE_PATH / "env_kb"))
        self._ready = True
        elapsed = (time.time() - t0) * 1000
        return {"chunks_count": len(chunks), "documents_count": len(raw), "processing_time_ms": elapsed}

    def load_knowledge_base(self) -> bool:
        try:
            self.search.load_index(str(settings.VECTOR_STORE_PATH / "env_kb"))
            self._ready = True
            return True
        except Exception as e:
            print(f"[RAG] 加载失败: {e}")
            return False

    def query(self, question: str, top_k=5, llm_config: LLMConfig = None,
              use_reranker=True, use_query_rewrite=True, use_multi_query=False) -> QueryResponse:
        if not self._ready:
            raise ValueError("知识库未加载")
        if not llm_config:
            raise ValueError("请提供 LLM 配置（provider + api_key）")
        t_total = time.time()

        # Query Transform
        rewritten = None
        multi_queries = []
        if use_query_rewrite:
            rewritten = self.transformer.rewrite_query(question, llm_config=llm_config)
        if use_multi_query:
            multi_queries = self.transformer.generate_multi_queries(question, llm_config=llm_config)

        # Hybrid Search
        t0 = time.time()
        docs, retrieval_ms = self.search.search(question, top_k=top_k, use_reranker=use_reranker)

        # Multi-query: 额外检索并合并
        if multi_queries:
            seen = set(d.page_content for d in docs)
            for mq in multi_queries[:2]:
                extra, _ = self.search.search(mq, top_k=3, use_reranker=False)
                for d in extra:
                    if d.page_content not in seen:
                        docs.append(d)
                        seen.add(d.page_content)

        # Build context
        context = "\n\n".join(f"[参考{i+1}]\n{d.page_content}" for i, d in enumerate(docs))
        prompt_text = self.prompt.format(context=context, question=question)

        # LLM generation
        t1 = time.time()
        llm = LLMFactory.create(llm_config, temperature=0.3, streaming=False)
        resp = llm.invoke([HumanMessage(content=prompt_text)])
        answer = resp.content if hasattr(resp, "content") else str(resp)
        gen_ms = (time.time() - t1) * 1000

        sources = [SourceDocument(content=d.page_content[:300], source=d.metadata.get("source", ""), page=d.metadata.get("page", 1)) for d in docs]

        # 确定实际使用的 provider 和 model
        provider_value = llm_config.provider.value if hasattr(llm_config.provider, "value") else llm_config.provider
        catalog = PROVIDER_CATALOG.get(llm_config.provider, {})
        model_used = llm_config.model or catalog.get("default_model", "")

        return QueryResponse(
            answer=answer, sources=sources,
            retrieval_time_ms=retrieval_ms, generation_time_ms=gen_ms,
            total_time_ms=(time.time() - t_total) * 1000,
            provider_used=provider_value,
            model_used=model_used,
            query_rewrite=rewritten, multi_queries=multi_queries or None,
        )

    def stream_query(self, question, llm_config: LLMConfig = None, **kwargs) -> Iterator[Dict]:
        if not self._ready:
            yield {"error": "知识库未加载"}
            return
        if not llm_config:
            yield {"error": "请提供 LLM 配置（provider + api_key）"}
            return

        use_reranker = kwargs.get("use_reranker", True)
        docs, _ = self.search.search(question, top_k=kwargs.get("top_k", 5), use_reranker=use_reranker)
        context = "\n\n".join(f"[参考{i+1}]\n{d.page_content}" for i, d in enumerate(docs))
        prompt_text = self.prompt.format(context=context, question=question)

        llm = LLMFactory.create(llm_config, temperature=0.3, streaming=True)
        for chunk in llm.stream([HumanMessage(content=prompt_text)]):
            content = chunk.content if hasattr(chunk, "content") else str(chunk)
            if content:
                yield {"token": content}

        sources = [{"content": d.page_content[:200], "source": d.metadata.get("source", ""), "page": d.metadata.get("page", 1)} for d in docs]
        yield {"sources": sources, "done": True}

    @property
    def is_ready(self):
        return self._ready


_engine = None

def get_rag_engine() -> RAGEngine:
    global _engine
    if _engine is None:
        _engine = RAGEngine()
    return _engine
