# -*- coding: utf-8 -*-
"""生成合成 HX-100 样例手册（PRD §46：公开演示建议自建 Sample Manual）。

按 PRD §48 演示数据集构建：覆盖 E104 报警（页 1）、启动前检查（页 2）、
E105 报警（页 3）。内容为自建演示文本，不含任何真实厂商机密。
运行：uv run --no-project python scripts/make_sample_manual.py [输出目录]
"""

import sys
from pathlib import Path

import pymupdf

PAGES: list[list[str]] = [
    [
        "HX-100 PEM Electrolyzer Maintenance Manual",
        "7.4 Error Code E104",
        "E104 - Cooling system temperature abnormal.",
        "Inspect coolant level and circulation pump operating state.",
        "Check the temperature sensor connection and signal continuity.",
        "Do not bypass protected interlocks during alarm inspection.",
    ],
    [
        "3.2 Pre-start Checklist",
        "Complete the cooling system check before startup.",
        "Confirm feed water supply meets the pre-start requirement.",
        "Inspect gas piping and connection integrity.",
        "Verify main power and control system status.",
        "Confirm all safety interlocks are cleared before enabling startup.",
    ],
    [
        "7.5 Error Code E105",
        "E105 - Feed water flow low.",
        "Check feed pump operation and inlet filter condition.",
        "Verify feed water conductivity is within the documented range.",
        "Escalate to component level diagnosis if the alarm persists.",
    ],
]


def build(out_path: Path) -> None:
    doc = pymupdf.open()
    for lines in PAGES:
        page = doc.new_page()
        y = 72
        for i, line in enumerate(lines):
            size = 18 if i == 0 else (13 if i == 1 else 10)
            page.insert_text((72, y), line, fontsize=size)
            y += 30 if i == 0 else (22 if i == 1 else 16)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_path))
    doc.close()
    print(f"sample manual written: {out_path} ({out_path.stat().st_size} bytes, {len(PAGES)} pages)")


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/sample/hx100-maintenance-v2.1.pdf")
    build(out)
