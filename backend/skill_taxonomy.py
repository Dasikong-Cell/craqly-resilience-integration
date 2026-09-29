"""Skill taxonomy registry for the craqly-resilience-integration skill.

This module is the single runnable artifact shipped in *this* repo. It materializes
the six classification tables documented in ``SKILL.md`` so they can be consumed by
an agent or by humans without depending on the (external) ``craqly-clone`` runtime code.

Design notes
------------
* Standard library only (``dataclasses``, ``typing``) — Py39 compatible.
* Each table owns ``TaxonomyRow`` records with ``id``, ``keywords`` and ``code_path``.
  For tables whose source markdown has extra columns (severity, phase, deliverable),
  that extra context is folded into ``keywords`` / ``code_path`` so no data is dropped.
* ``validate_skill_taxonomy`` guarantees taxonomy IDs are unique across all tables.
"""

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class TaxonomyRow:
    """A single classification entry."""

    id: str
    keywords: List[str]
    code_path: str


@dataclass
class TaxonomyTable:
    """A named table of :class:`TaxonomyRow` records."""

    name: str
    rows: List[TaxonomyRow] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Render this table as a Markdown document fragment."""
        lines = ["# " + self.name, "", "| id | keywords | code_path |", "| --- | --- | --- |"]
        for row in self.rows:
            kw = ", ".join(row.keywords)
            lines.append("| {0} | {1} | {2} |".format(row.id, kw, row.code_path))
        lines.append("")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Raw data transcribed verbatim from SKILL.md (no interpretation).
# ---------------------------------------------------------------------------

_OCR_ROWS = [
    TaxonomyRow(
        "backend_none",
        ["ocr 后端", "ocr引擎", "ocr engine", "ocr backend"],
        "backend/resilient_ocr.py::recognize_with_fallback, backend/resilient_ocr.py::_check_ocr_available",
    ),
    TaxonomyRow(
        "preprocess_failure",
        ["预处理", "preprocess", "preprocess_image", "图片预处理"],
        "backend/screenshot.py::preprocess_image, backend/resilient_ocr.py::recognize_with_fallback",
    ),
    TaxonomyRow(
        "empty_output",
        ["空文本", "empty text", "空结果", "empty output"],
        "backend/resilient_ocr.py::_validate_ocr, backend/resilient_ocr.py::_hint_for_empty",
    ),
    TaxonomyRow(
        "short_text",
        ["短文本", "short text", "字符少", "1-2 字符"],
        "backend/resilient_ocr.py::_validate_ocr, backend/ocr_post_process.py",
    ),
    TaxonomyRow(
        "low_contrast",
        ["对比度", "contrast", "模糊", "blur"],
        "backend/screenshot.py::preprocess_image, backend/resilient_ocr.py::recognize_with_fallback",
    ),
    TaxonomyRow(
        "code_mojibake",
        ["代码", "code", "符号混淆", "mojibake"],
        "backend/ocr_post_process.py::fix_code_symbols",
    ),
]

_LLM_ROWS = [
    TaxonomyRow(
        "first_token_timeout",
        ["首token", "first token", "首 token", "思考中"],
        "backend/resilient_llm.py::chat_stream_with_budget, backend/llm_agent.py::LLMAgent.chat_stream_isolated",
    ),
    TaxonomyRow(
        "full_timeout",
        ["超时", "timeout", "响应超时", "完整响应"],
        "backend/resilient_llm.py::chat_stream_with_budget",
    ),
    TaxonomyRow(
        "degradation_failure",
        ["降级", "degradation", "降级失效", "并行"],
        "backend/resilient_llm.py::parallel_with_template",
    ),
    TaxonomyRow(
        "cache_miss_fallback",
        ["缓存", "cache", "缓存未命中", "cache miss"],
        "backend/answer_cache.py::AnswerCache, backend/algorithm_cache.py::check_cache",
    ),
    TaxonomyRow(
        "token_overrun",
        ["token", "max_tokens", "截断", "truncation"],
        "config.py::llm_max_tokens, backend/resilient_llm.py",
    ),
]

_WS_ROWS = [
    TaxonomyRow(
        "initial_connect_fail",
        ["首次连接", "initial connect", "连接失败", "ws连接"],
        "renderer.js::connectWebSocket, backend/server.py::ws_manager",
    ),
    TaxonomyRow(
        "disconnect_timeout",
        ["断开", "disconnect", "超时断开", "timeout disconnect"],
        "renderer.js::wsHeartbeat",
    ),
    TaxonomyRow(
        "reconnect_exhausted",
        ["重连", "reconnect", "重连次数", "retry"],
        "renderer.js::reconnectWS",
    ),
    TaxonomyRow(
        "message_ordering",
        ["顺序", "ordering", "顺序错乱", "乱序"],
        "renderer.js::handleWsMessage",
    ),
]

# Anti-Pattern: source columns are (severity, id, 说明).
# severity is folded into ``keywords``; the 说明 description goes into ``code_path``.
_ANTI_PATTERN_ROWS = [
    TaxonomyRow("silently_swallow_error", ["critical"], "静默错误，用户完全无感"),
    TaxonomyRow("no_hint_on_empty", ["critical"], "空结果无任何提示"),
    TaxonomyRow("single_entry_fix", ["high"], "只修单入口，其他入口仍有 bug"),
    TaxonomyRow("mix_refactor_in_fix", ["high"], "修复中夹带无关重构"),
    TaxonomyRow("skip_reverse_proof", ["high"], "跳过反向验证，无法证明 fix 有效"),
    TaxonomyRow("hardcoded_threshold", ["medium"], "硬编码阈值（如 len>=3）"),
    TaxonomyRow("missing_errors_field", ["medium"], "FallbackResult 缺少 errors 字段"),
    TaxonomyRow("expose_internal_name", ["low"], "暴露内部名称给用户"),
    TaxonomyRow("missing_code_convention", ["low"], "不遵循代码约定"),
]

# SLO: source columns are (检查阶段, 指标 ID, 触发关键词).
# 指标 ID -> id, 触发关键词 -> keywords, 检查阶段 -> code_path.
_SLO_ROWS = [
    TaxonomyRow("p50_latency", ["p50", "P50", "first token p50"], "pre_merge"),
    TaxonomyRow("p99_latency", ["p99", "P99", "first token p99"], "pre_merge"),
    TaxonomyRow("auto_recovery_rate", ["自动恢复", "auto recovery", "recovery rate"], "post_deploy"),
    TaxonomyRow("auto_degradation_rate", ["自动降级", "auto degradation", "degradation rate"], "post_deploy"),
    TaxonomyRow("reconnect_rate", ["重连率", "reconnect rate", "ws reconnect"], "monitoring"),
    TaxonomyRow("first_token_p99", ["首token", "first token p99", "token latency"], "monitoring"),
]

# Workflow: source columns are (Step ID, 阶段, 子任务 ID, 产出物).
# When 子任务 ID == "—" the Step ID is the leaf key. Step ID + 阶段 -> keywords, 产出物 -> code_path.
_WORKFLOW_ROWS = [
    TaxonomyRow("symptom", ["triage"], "症状描述文档"),
    TaxonomyRow("expected", ["triage"], "症状描述文档"),
    TaxonomyRow("severity", ["triage"], "症状描述文档"),
    TaxonomyRow("repro_path", ["triage"], "症状描述文档"),
    TaxonomyRow("primary_specialist", ["routing", "triage"], "路由决策记录"),
    TaxonomyRow("secondary_specialist", ["routing", "triage"], "路由决策记录"),
    TaxonomyRow("write_test", ["reproduce"], "Failing test + 错误日志"),
    TaxonomyRow("verify_fail", ["reproduce"], "Failing test + 错误日志"),
    TaxonomyRow("capture_error", ["reproduce"], "Failing test + 错误日志"),
    TaxonomyRow("list_hypotheses", ["hypothesize"], "假设列表 + 优先级"),
    TaxonomyRow("rank", ["hypothesize"], "假设列表 + 优先级"),
    TaxonomyRow("select_primary", ["hypothesize"], "假设列表 + 优先级"),
    TaxonomyRow("identify_paths", ["fix"], "代码 diff"),
    TaxonomyRow("apply_fix", ["fix"], "代码 diff"),
    TaxonomyRow("update_routes", ["fix"], "代码 diff"),
    TaxonomyRow("green", ["verify"], "验证证据链"),
    TaxonomyRow("reverse", ["verify"], "验证证据链"),
    TaxonomyRow("wider", ["verify"], "验证证据链"),
    TaxonomyRow("full", ["verify"], "验证证据链"),
    TaxonomyRow(
        "sem_deliverables",
        ["deliver"],
        "PRR matrix, observability spec, alert policy, component map, timeout budget",
    ),
    TaxonomyRow(
        "dev_fix_artifact",
        ["deliver"],
        "Symptom/Expected, hypotheses, root cause, fix diff, verification, test path, pattern analysis, follow-ups",
    ),
]


# ---------------------------------------------------------------------------
# Public getters
# ---------------------------------------------------------------------------

def get_ocr_table() -> TaxonomyTable:
    return TaxonomyTable("OCR 场景二级分类", list(_OCR_ROWS))


def get_llm_table() -> TaxonomyTable:
    return TaxonomyTable("LLM 场景二级分类", list(_LLM_ROWS))


def get_ws_table() -> TaxonomyTable:
    return TaxonomyTable("WS 场景二级分类", list(_WS_ROWS))


def get_anti_pattern_table() -> TaxonomyTable:
    return TaxonomyTable("Anti-Pattern 严重程度分类", list(_ANTI_PATTERN_ROWS))


def get_slo_table() -> TaxonomyTable:
    return TaxonomyTable("SLO 指标检查阶段分类", list(_SLO_ROWS))


def get_workflow_table() -> TaxonomyTable:
    return TaxonomyTable("Workflow Step 子任务分类", list(_WORKFLOW_ROWS))


def _all_tables() -> List[TaxonomyTable]:
    return [
        get_ocr_table(),
        get_llm_table(),
        get_ws_table(),
        get_anti_pattern_table(),
        get_slo_table(),
        get_workflow_table(),
    ]


def validate_skill_taxonomy() -> Dict[str, object]:
    """Validate the taxonomy registry.

    Returns a result dict with ``valid: bool`` and ``errors: List[str]``.
    Currently checks that every taxonomy ID is unique across all tables.
    """
    errors: List[str] = []
    seen: Dict[str, str] = {}
    for table in _all_tables():
        for row in table.rows:
            if row.id in seen:
                errors.append(
                    "duplicate taxonomy id '{0}' in table '{1}' (also in '{2}')".format(
                        row.id, table.name, seen[row.id]
                    )
                )
            else:
                seen[row.id] = table.name
    return {"valid": len(errors) == 0, "errors": errors}


if __name__ == "__main__":
    import json

    print(json.dumps(validate_skill_taxonomy(), ensure_ascii=False))
    for table in _all_tables():
        print(table.to_markdown())
