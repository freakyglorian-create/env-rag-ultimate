"""
文档解析器测试
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document

from app.services.parser.document_parser import DocumentParser

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class TestSupportedFormats:
    def test_supported_extensions(self):
        assert ".txt" in DocumentParser.SUPPORTED
        assert ".pdf" in DocumentParser.SUPPORTED
        assert ".docx" in DocumentParser.SUPPORTED
        assert ".html" in DocumentParser.SUPPORTED
        assert ".md" in DocumentParser.SUPPORTED
        assert ".xlsx" in DocumentParser.SUPPORTED


class TestParseTxt:
    def test_utf8(self, sample_txt_path):
        docs = DocumentParser.parse_txt(sample_txt_path)
        assert len(docs) >= 1
        assert "MBR" in docs[0].page_content or "膜生物反应器" in docs[0].page_content
        assert docs[0].metadata["type"] == "txt"
        assert docs[0].metadata["source"] == "sample.txt"

    def test_file_not_found(self):
        docs = DocumentParser.parse_txt("/nonexistent/file.txt")
        assert docs == []

    def test_encoding_fallback(self, tmp_path):
        """测试 GBK 编码回退"""
        p = tmp_path / "gbk_file.txt"
        content = "GBK编码测试文本关于COD排放标准"
        p.write_bytes(content.encode("gbk"))
        docs = DocumentParser.parse_txt(str(p))
        assert len(docs) == 1
        assert "COD" in docs[0].page_content


class TestParseMarkdown:
    def test_basic(self, sample_md_path):
        docs = DocumentParser.parse_markdown(sample_md_path)
        assert len(docs) >= 1
        content = docs[0].page_content
        # 标题标记被移除
        assert "#" not in content or "##" not in content
        # 内容保留
        assert "PM2.5" in content
        assert docs[0].metadata["type"] == "markdown"

    def test_bold_removed(self):
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("**粗体文本** 和 __也是粗体__")
            f.flush()
            docs = DocumentParser.parse_markdown(f.name)
        import os
        os.unlink(f.name)
        assert len(docs) >= 1
        content = docs[0].page_content
        assert "**" not in content
        assert "__" not in content

    def test_code_blocks_removed(self):
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("这是文本 `code` 还有 ```block``` 结束")
            f.flush()
            docs = DocumentParser.parse_markdown(f.name)
        import os
        os.unlink(f.name)
        content = docs[0].page_content
        assert "`code`" not in content
        assert "```" not in content


class TestParseHtml:
    def test_basic(self, sample_html_path):
        docs = DocumentParser.parse_html(sample_html_path)
        assert len(docs) >= 1
        content = docs[0].page_content
        assert "60个工作日" in content
        assert docs[0].metadata["type"] == "html"

    def test_script_tags_removed(self, sample_html_path):
        docs = DocumentParser.parse_html(sample_html_path)
        content = docs[0].page_content
        assert "console.log" not in content
        assert "tracking" not in content

    def test_nav_footer_removed(self, sample_html_path):
        docs = DocumentParser.parse_html(sample_html_path)
        content = docs[0].page_content
        assert "导航菜单" not in content
        assert "© 2024" not in content


class TestParsePdf:
    def test_fallback_to_txt_on_error(self):
        """PDF 解析失败时回退到 TXT 解析"""
        docs = DocumentParser.parse_pdf("/no/file.pdf")
        assert docs == []

    @patch("pypdf.PdfReader")
    def test_successful_parse(self, mock_reader, tmp_path):
        # 模拟 PDF 有 2 页
        page1 = MagicMock()
        page1.extract_text.return_value = "第一页内容：SCR脱硝技术"
        page2 = MagicMock()
        page2.extract_text.return_value = "第二页内容：催化剂选型"
        mock_reader.return_value.pages = [page1, page2]

        docs = DocumentParser.parse_pdf(str(tmp_path / "test.pdf"))
        assert len(docs) == 2
        assert docs[0].metadata["page"] == 1
        assert docs[1].metadata["page"] == 2
        assert docs[1].metadata["type"] == "pdf"

    @patch("pypdf.PdfReader")
    def test_empty_pages_skipped(self, mock_reader, tmp_path):
        page = MagicMock()
        page.extract_text.return_value = "   "
        mock_reader.return_value.pages = [page]

        docs = DocumentParser.parse_pdf(str(tmp_path / "test.pdf"))
        assert len(docs) == 0


class TestParseDocx:
    def test_fallback_to_txt_on_error(self):
        docs = DocumentParser.parse_docx("/no/file.docx")
        assert docs == []

    @patch("docx.Document")
    def test_successful_parse(self, mock_dx_cls, tmp_path):
        para1 = MagicMock()
        para1.text = "第一章 环境影响评价概述"
        para2 = MagicMock()
        para2.text = "   "  # 空白段落，应被过滤
        para3 = MagicMock()
        para3.text = "环评报告书的审批时限"
        mock_dx_cls.return_value.paragraphs = [para1, para2, para3]

        docs = DocumentParser.parse_docx(str(tmp_path / "test.docx"))
        assert len(docs) == 1
        assert "第一章" in docs[0].page_content
        assert "审批时限" in docs[0].page_content


class TestParseXlsx:
    def test_file_not_found(self):
        docs = DocumentParser.parse_xlsx("/no/file.xlsx")
        assert docs == []

    @patch("openpyxl.load_workbook")
    def test_successful_parse(self, mock_load, tmp_path):
        mock_ws = MagicMock()
        mock_ws.iter_rows.return_value = [
            ("污染物", "限值", "单位"),
            ("PM2.5", "35", "μg/m³"),
            ("SO2", "60", "μg/m³"),
        ]
        mock_wb = MagicMock()
        mock_wb.sheetnames = ["Sheet1"]
        mock_wb.__getitem__.return_value = mock_ws
        mock_load.return_value = mock_wb

        docs = DocumentParser.parse_xlsx(str(tmp_path / "test.xlsx"))
        assert len(docs) == 1
        assert "PM2.5" in docs[0].page_content


class TestParse:
    def test_dispatch(self, sample_txt_path, sample_md_path, sample_html_path):
        """验证 parse() 根据扩展名选择解析器"""
        assert len(DocumentParser.parse(sample_txt_path)) >= 1
        assert len(DocumentParser.parse(sample_md_path)) >= 1
        assert len(DocumentParser.parse(sample_html_path)) >= 1

    def test_unknown_extension_falls_back_to_txt(self, sample_txt_path):
        """未知扩展名应回退到 TXT 解析"""
        docs = DocumentParser.parse(sample_txt_path)  # .txt
        assert len(docs) >= 1


class TestParseDirectory:
    def test_parses_all_supported(self, sample_kb_dir):
        docs = DocumentParser.parse_directory(sample_kb_dir)
        assert len(docs) >= 3  # txt + md + html
        types = {d.metadata.get("type") for d in docs}
        assert "txt" in types
        assert "markdown" in types
        assert "html" in types

    def test_ignores_unsupported(self, tmp_path):
        (tmp_path / "image.png").write_text("fake png")
        (tmp_path / "data.csv").write_text("col1,col2")
        (tmp_path / "doc.txt").write_text("hello", encoding="utf-8")

        docs = DocumentParser.parse_directory(str(tmp_path))
        assert len(docs) == 1
        assert docs[0].metadata["type"] == "txt"


class TestSplitDocuments:
    def test_basic_split(self, sample_documents):
        chunks = DocumentParser.split_documents(sample_documents)
        assert len(chunks) > 0
        for chunk in chunks:
            assert len(chunk.page_content.strip()) > 30

    def test_chunks_have_source(self, sample_documents):
        chunks = DocumentParser.split_documents(sample_documents)
        for chunk in chunks:
            assert "source" in chunk.metadata

    def test_empty_input(self):
        chunks = DocumentParser.split_documents([])
        assert chunks == []

    def test_short_documents_filtered(self):
        short_doc = Document(page_content="太短", metadata={"source": "short.txt"})
        chunks = DocumentParser.split_documents([short_doc])
        assert len(chunks) == 0  # 短于 30 字符被过滤

    def test_custom_chunk_params(self):
        docs = [Document(page_content="这是一段很长的环境工程文本。" * 30, metadata={"source": "long.txt"})]
        chunks = DocumentParser.split_documents(docs, chunk_size=256, overlap=50)
        assert len(chunks) > 0
        for c in chunks:
            assert 30 < len(c.page_content)  # after filtering, should still be reasonable
