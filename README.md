#resilience-integration

End-to-end resilience workflow skill for **craqly-clone** — a local AI coding interview platform.

When users report failure symptoms like "OCR 返回空文本", "AI 解答卡住", or "WS 断连", this skill automates the full diagnosis→fix→verify→deliver pipeline.

## What It Does

1. **Triage & Routing**: Classifies symptoms to the right staff-engineer-mode specialist
2. **Reproduce**: Writes failing regression tests before any code change
3. **Hypothesize**: Lists 3-5 root-cause hypotheses across different dimensions
4. **Surgical Fix**: Touches only root-cause paths — never refactors adjacent code
5. **Red-Green-Red Verify**: Proves regression tests catch the bug (reverse-proof)
6. **SEM Deliverables**: Produces PRR matrix, observability dashboard spec, alert policy
7. **Artifact**: Writes structured dev-fix artifact to `.claude/artifacts/fixes/`

## When to Invoke

- User sends a screenshot showing **OCR empty text** ("OCR 返回空文本")
- User reports AI answer taking too long / **"思考中" stuck**
- User mentions **WebSocket reconnect** issues
- User asks to write OCR/LLM three-level degradation into runnable code
- Any reliability/resilience concern in craqly-clone backend or renderer

## Key Modules (目标运行时代码 — 不在本仓库)

> **重要说明**：下表列出的模块是**目标运行时代码**，它们属于**外部的 `craqly-clone` 项目**，并不在本仓库 (`craqly-resilience-integration`) 中。本仓库目前仅包含文档（SKILL.md / README.md）以及一个可运行的分类注册表模块 `backend/skill_taxonomy.py`。SKILL.md 中的工作流假设这些外部模块已存在于 `craqly-clone` 里。

| File (in craqly-clone) | Purpose |
|---|---|
| `backend/fallback.py` | Timeout circuit breaker + serial degradation + parallel race + FallbackStats |
| `backend/resilient_ocr.py` | OCR 3-level fallback (primary→enhanced→cache) with 4-tier hint |
| `backend/resilient_llm.py` | LLM parallel primary/fast model race + template fallback |
| `backend/resilient_asr.py` | ASR engine switch chain (Paraformer→Whisper→empty) |
| `backend/answer_cache.py` | 3-level answer cache (memory LRU→JSON file→Hot 100 preload) |
| `frontend/src/composables/useWebSocket.ts` | Exponential backoff + pending message cache |

本仓库实际可运行的代码：

| File (in this repo) | Purpose |
|---|---|
| `backend/skill_taxonomy.py` | 关键词驱动的分类注册表（OCR/LLM/WS/Anti-Pattern/SLO/Workflow 六张表）+ 校验 |
| `tests/test_skill_taxonomy.py` | 针对分类注册表的 pytest 单元测试 |

## SLO Acceptance

| Metric | Target |
|---|---|
| P50 first-token latency | < 500ms |
| P99 first-token latency | < 1000ms |
| OCR auto-recovery rate | > 95% |
| LLM auto-degradation rate | > 99% |
| WS auto-reconnect rate | > 99% |

All 5 indicators exposed via `GET /api/metrics` → `acceptance` dict.

## Validate the taxonomy

This repo ships a runnable classification registry in `backend/skill_taxonomy.py`.
You can verify it locally without any external dependencies:

```bash
# 1) Validate that all taxonomy IDs are globally unique
python -c "from backend.skill_taxonomy import validate_skill_taxonomy; print(validate_skill_taxonomy())"

# 2) Run the unit tests
pytest

# 3) (optional) Print every table as Markdown
python -c "from backend import skill_taxonomy as s; [print(t.to_markdown()) for t in [s.get_ocr_table(), s.get_llm_table(), s.get_ws_table(), s.get_anti_pattern_table(), s.get_slo_table(), s.get_workflow_table()]]"
```

> **状态说明**：本仓库目前**不包含** 51/53 个通过的测试套件——那些数字来自 SKILL.md 中对 `craqly-clone` 外部运行代码的期望，并非本仓库现状。本仓库现有 `tests/test_skill_taxonomy.py` 中少量真实测试，运行 `pytest` 即可查看实际通过数量。

## License

MIT
