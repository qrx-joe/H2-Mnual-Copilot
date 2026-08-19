# -*- coding: utf-8 -*-
"""Phase 2 风险验证 V-1：RRF 融合与错误代码路由（纯逻辑，无第三方依赖）。

验证对象（docs/architecture/system-design.md §3.1 / §9）：
1. Reciprocal Rank Fusion：两路排名融合后，双路命中的文档应排在仅单路命中之前。
2. 错误代码 regex 路由（技术规范 §38）：^[A-Z]{1,4}[-_]?\\d{2,6}$ 命中 E104/HX-100
   类代码，拒绝自然语言问题；小写输入先规范化再匹配（§37 normalize）。

本脚本属于隔离验证代码，验证完成后可整体删除，不得被产品代码引用。
"""

import re
import sys

ERROR_CODE_RE = re.compile(r"^[A-Z]{1,4}[-_]?\d{2,6}$")
RRF_K = 60  # RRF 常数，业界通用值


def normalize(text: str) -> str:
    """查询规范化：去首尾空白、统一大写（技术规范 §37 normalize 步骤）。"""
    return text.strip().upper()


def is_error_code(query: str) -> bool:
    return bool(ERROR_CODE_RE.match(normalize(query)))


def reciprocal_rank_fusion(*ranked_lists: list[str]) -> list[tuple[str, float]]:
    """RRF：score(d) = Σ_lists 1 / (k + rank_d)。

    rank 从 1 开始；未出现在某列表中的文档不贡献该项。
    """
    scores: dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, doc_id in enumerate(ranked, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (RRF_K + rank)
    return sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))


def check(label: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}" + (f" — {detail}" if detail else ""))
    if not condition:
        sys.exit(1)


def main() -> None:
    # --- 错误代码路由 ---
    check("E104 命中错误代码路由", is_error_code("E104"))
    check("小写 e104 规范化后命中", is_error_code("e104"))
    check("HX-100 命中（型号走同一精确词法路径）", is_error_code("HX-100"))
    check("E-12 命中（带连字符短代码）", is_error_code("E-12"))
    check("自然语言问题不命中", not is_error_code("冷却系统温度太高怎么办"))
    check("普通英文短语不命中", not is_error_code("what is E series"))
    check("纯数字不命中", not is_error_code("12345"))
    check("带空格的多词不命中", not is_error_code("E104 AND E105"))

    # --- RRF 融合 ---
    lexical = ["chunk_a", "chunk_b", "chunk_c"]          # 词法命中：错误代码表页
    dense = ["chunk_b", "chunk_d", "chunk_a"]            # 语义命中：故障排查段
    fused = reciprocal_rank_fusion(lexical, dense)

    order = [doc for doc, _ in fused]
    check(
        "双路命中的 chunk_b 排第一",
        order[0] == "chunk_b",
        f"融合顺序: {order}",
    )
    check(
        "双路命中的 chunk_a 排在仅单路命中的 chunk_c/chunk_d 之前",
        order.index("chunk_a") < min(order.index("chunk_c"), order.index("chunk_d")),
        f"融合顺序: {order}",
    )
    check(
        "融合结果包含两路全部候选且无重复",
        sorted(order) == ["chunk_a", "chunk_b", "chunk_c", "chunk_d"],
    )

    print("\nV-1 全部通过：RRF 融合与错误代码路由行为符合系统设计 §3.1 预期。")


if __name__ == "__main__":
    main()
