import os

files = {
    r"app\services\rag\engine.py": [
        ("from langchain.schema import Document, HumanMessage", "from langchain_core.documents import Document\nfrom langchain_core.messages import HumanMessage"),
    ],
    r"app\services\llm\gateway.py": [
        ("from langchain.schema import BaseMessage, HumanMessage, SystemMessage", "from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage"),
    ],
    r"app\services\parser\document_parser.py": [
        ("from langchain.schema import Document", "from langchain_core.documents import Document"),
    ],
    r"app\services\rag\hybrid_search.py": [
        ("from langchain.schema import Document", "from langchain_core.documents import Document"),
    ],
    r"app\services\query_transform\transformer.py": [
        ("from langchain.schema import HumanMessage", "from langchain_core.messages import HumanMessage"),
    ],
}

for filepath, replacements in files.items():
    if not os.path.exists(filepath):
        print(f"跳过: {filepath} (不存在)")
        continue
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            print(f"已修复: {filepath}")
        else:
            print(f"无需修改: {filepath}")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("修复完成！")
