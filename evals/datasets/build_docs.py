# -*- coding: utf-8 -*-
"""评测用合成文档集（PRD §46/§48：演示数据自建，非敏感）。

四份文档对应 PRD 演示集构成（Operation/Maintenance/Safety/Error Codes），
内容与 evals/datasets/golden.jsonl 的期望答案一一对应——保证评测可判定。
"""

import pymupdf

DOCS: list[dict] = [
    {
        "device_id": "hx100",
        "title": "HX-100 Operation Manual",
        "document_type": "OPERATION",
        "version": "2.1",
        "pages": [
            [
                "1 Overview",
                "The HX-100 PEM electrolyzer supports grid scale hydrogen production.",
                "The manual is written in English for international service engineers.",
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
                "4.1 Operating Parameters",
                "Normal operating pressure is 1.5 MPa.",
                "Pre-start pressure is 1.2 MPa.",
                "Coolant temperature range is 20 to 40 degrees Celsius.",
            ],
        ],
    },
    {
        "device_id": "hx100",
        "title": "HX-100 Maintenance Manual",
        "document_type": "MAINTENANCE",
        "version": "2.1",
        "pages": [
            [
                "7.4 Error Code E104",
                "E104 - Cooling system temperature abnormal.",
                "Inspect coolant level and circulation pump operating state.",
                "Check the temperature sensor connection and signal continuity.",
                "Do not bypass protected interlocks during alarm inspection.",
            ],
            [
                "7.5 Error Code E105",
                "E105 - Feed water flow low.",
                "Check feed pump operation and inlet filter condition.",
                "Verify feed water conductivity is within the documented range.",
            ],
            [
                "7.6 Error Code E106",
                "E106 - Hydrogen leak detected.",
                "Evacuate the area and close the manual isolation valve.",
                "Do not operate electrical equipment near the hydrogen leak.",
            ],
        ],
    },
    {
        "device_id": "hx100",
        "title": "HX-100 Safety Guide",
        "document_type": "SAFETY",
        "version": "1.0",
        "pages": [
            [
                "2.1 Safety Interlocks",
                "The HX-100 has five safety interlocks.",
                "Never bypass a safety interlock.",
                "Interlock bypass requires written approval from the safety officer.",
            ],
            [
                "3.4 Electrical Safety",
                "Disconnect main power before service.",
                "Lock out and tag out the breaker before electrical work.",
            ],
        ],
    },
    {
        "device_id": "hx100",
        "title": "HX-100 Error Code Reference",
        "document_type": "ERROR_CODES",
        "version": "2.1",
        "pages": [
            [
                "Error Codes",
                "E104 Cooling system temperature abnormal.",
                "E105 Feed water flow low.",
                "E106 Hydrogen leak detected.",
                "E107 Stack voltage low.",
            ],
            [
                "Error Codes continued",
                "E108 Water quality out of range.",
                "E110 Power supply fault.",
            ],
        ],
    },
]


def build_pdf_bytes(pages: list[list[str]]) -> bytes:
    """与 scripts/make_sample_manual.py 相同的版式：每页一组 (heading, body)。"""
    import tempfile
    from pathlib import Path

    doc = pymupdf.open()
    for lines in pages:
        page = doc.new_page()
        y = 72
        for i, line in enumerate(lines):
            page.insert_text((72, y), line, fontsize=16 if i == 0 else 10)
            y += 24 if i == 0 else 16
    tmp = Path(tempfile.mktemp(suffix=".pdf"))
    doc.save(str(tmp))
    doc.close()
    return tmp.read_bytes()
