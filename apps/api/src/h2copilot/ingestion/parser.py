"""解析与分块（技术规范 §20–§26）。

V-2 验证结论（scratch/phase2）：必须用 page_chunks=True 取页码
（metadata.page_number，1 起算）；默认整体模式无页码，不能用于引用。
MinerU fallback：真实扫描件到位（Q-011）后接入；当前对解析失败直接 FAILED。
"""

import re
from pathlib import Path

import pymupdf4llm

from h2copilot.llm.providers import ParsedDocument, ParsedPage


class PyMuPDFParser:
    """文本型 PDF → 分页 Markdown。"""

    name = "pymupdf4llm-v1"

    async def parse(self, file_path: Path) -> ParsedDocument:
        pages = pymupdf4llm.to_markdown(str(file_path), page_chunks=True)
        parsed = ParsedDocument()
        for p in pages:
            parsed.pages.append(
                ParsedPage(page_number=int(p["metadata"]["page_number"]), text=p["text"])
            )
        return parsed


# ---------- 结构化分块 ----------

# 目标 350–700 token（技术规范 §26）。中文按字符≈0.7 token、英文按 4 字符≈1 token 估算，
# 这里用保守的字符窗口近似，并在标题边界优先切分。
_TARGET_CHARS = 1200
_OVERLAP_CHARS = 150


def split_sections(page_text: str) -> list[tuple[str, str]]:
    """按 Markdown 标题切段，返回 (section_path, content)。"""
    sections: list[tuple[str, str]] = []
    current_path: list[str] = []
    buf: list[str] = []

    for line in page_text.splitlines():
        heading = re.match(r"^(#{1,4})\s+(.*)$", line)
        if heading:
            if buf:
                sections.append((" / ".join(current_path), "\n".join(buf).strip()))
                buf = []
            level = len(heading.group(1))
            title = heading.group(2).strip()
            current_path = current_path[: level - 1]
            current_path.append(title)
        else:
            buf.append(line)
    if buf:
        sections.append((" / ".join(current_path), "\n".join(buf).strip()))
    return [(p, c) for p, c in sections if c]


def chunk_page(page: ParsedPage) -> list[tuple[int, str, str]]:
    """单页 → [(chunk_index 前置为空, section_path, content)]，内容按窗口二次切分。

    保持错误代码/警告等原子块完整（§26）：以句号为界优先，不跨段硬切。
    """
    results: list[tuple[int, str, str]] = []
    for section_path, content in split_sections(page.text):
        start = 0
        while start < len(content):
            window = content[start : start + _TARGET_CHARS]
            if len(window) == _TARGET_CHARS:
                # 在窗口尾部找句子边界，避免半句截断
                cut = max(window.rfind(". "), window.rfind("。"), window.rfind("\n"))
                if cut > _TARGET_CHARS // 2:
                    window = window[: cut + 1]
            window = window.strip()
            if len(window) > 20:
                results.append((page.page_number, section_path, window))
            start += max(len(window), _TARGET_CHARS - _OVERLAP_CHARS)
    return results
