# -*- coding: utf-8 -*-
"""Phase 2 风险验证 V-2：PyMuPDF4LLM 解析机制（合成 PDF 往返）。

验证对象（docs/architecture/system-design.md §3.2 / §9）：
1. pymupdf4llm 可安装并运行（uv 临时环境）。
2. 文本型 PDF → Markdown 转换保留标题结构与正文内容。
3. **页码溯源**：默认 to_markdown() 不带页码标记；必须使用 page_chunks=True
   获得带 metadata.page 的分页结构——这是 Citation 页码（FR-003/007）的
   数据来源，ingestion 管线必须采用该模式。（V-2 首轮运行发现的修正项）

证据边界：这是"机制级"验证（库可用、结构与页码保留）；对真实工业手册
（多栏、表格、扫描件）的解析质量仍属【待验证】，需要演示 PDF（Q-011）后
评估，并据此决定 MinerU fallback 的触发条件。

本脚本属于隔离验证代码，验证完成后可整体删除，不得被产品代码引用。
运行：uv run --no-project --with pymupdf4llm python scratch/phase2/verify_parser.py
"""

import sys
import tempfile
from pathlib import Path

import pymupdf  # 同时用它生成合成 PDF（fitz 别名已废弃）
import pymupdf4llm


def build_sample_pdf(path: Path) -> None:
    """生成 2 页带标题层级的文本型 PDF，模拟手册的章节结构。"""
    doc = pymupdf.open()
    page1 = doc.new_page()
    page1.insert_text((72, 90), "HX-100 Maintenance Manual", fontsize=16)
    page1.insert_text((72, 130), "7.4 Error Code E104", fontsize=12)
    page1.insert_text(
        (72, 160),
        "E104 - Cooling system temperature abnormal. Inspect coolant level,",
        fontsize=10,
    )
    page1.insert_text(
        (72, 175),
        "circulation pump operating state and temperature sensor connection.",
        fontsize=10,
    )
    page2 = doc.new_page()
    page2.insert_text((72, 90), "7.5 Error Code E105", fontsize=12)
    page2.insert_text((72, 120), "E105 - Feed water flow low. Check feed pump.", fontsize=10)
    doc.save(str(path))
    doc.close()


def check(label: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}" + (f" — {detail}" if detail else ""))
    if not condition:
        sys.exit(1)


def main() -> None:
    print(f"pymupdf4llm 版本: {getattr(pymupdf4llm, '__version__', 'unknown')}")

    with tempfile.TemporaryDirectory() as tmp:
        pdf_path = Path(tmp) / "sample.pdf"
        build_sample_pdf(pdf_path)
        check("合成 PDF 已生成", pdf_path.stat().st_size > 0, f"{pdf_path.stat().st_size} bytes")

        # 模式一：默认整体 Markdown（用于人工查看/调试）
        md = pymupdf4llm.to_markdown(str(pdf_path))
        md_lower = md.lower()
        check("章节标题保留", "error code e104" in md_lower)
        check("正文关键内容保留", "cooling system temperature abnormal" in md_lower)
        check("第二页内容保留（页面切分不丢内容）", "feed water flow low" in md_lower)
        check(
            "输出为结构化 Markdown（含标题标记）",
            any(line.lstrip().startswith("#") for line in md.splitlines()),
        )

        # 模式二：page_chunks=True 分页结构（ingestion 采用，页码溯源依据）
        pages = pymupdf4llm.to_markdown(str(pdf_path), page_chunks=True)
        check("page_chunks 返回分页列表", isinstance(pages, list) and len(pages) == 2)
        page_numbers = [p["metadata"]["page_number"] for p in pages]
        check(
            "每页携带 page_number 元数据（从 1 计，可直接作引用页码）",
            page_numbers == [1, 2],
            f"{page_numbers}",
        )
        check(
            "E104 内容确实归属第 1 页（引用页码=1）",
            "e104" in pages[0]["text"].lower() and "e105" not in pages[0]["text"].lower(),
        )
        check(
            "E105 内容确实归属第 2 页",
            "e105" in pages[1]["text"].lower(),
        )

    print("\nV-2 机制级通过：PyMuPDF4LLM 可安装、可运行、结构与页码信息保留。")
    print("结论：ingestion 使用 page_chunks=True，页码取 metadata.page_number（1 起算）。")
    print("注意：真实手册质量（表格/扫描件/多栏）仍待演示 PDF 验证（Q-011）。")


if __name__ == "__main__":
    main()
