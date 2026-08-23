---
name: "craqly-resilience-integration"
description: "Resilience integration workflow for craqly-clone OCR/LLM/WS failures. Invoke when user reports OCR empty text, LLM slow/first-token timeout, or WebSocket disconnect with a screenshot."
---

# Craqly Resilience Integration

End-to-end workflow for diagnosing, fixing, verifying, and delivering resilience mechanisms when the user reports a failure symptom in craqly-clone (OCR empty, LLM slow first token, WS disconnect).

## When to Invoke

- User sends a screenshot showing OCR returning empty text ("OCR 返回空文本")
- User reports AI answer taking too long / "思考中" stuck
- User mentions WebSocket reconnect issues
- User asks for "把 OCR/LLM 三级降级写成完整可运行代码"
- Any reliability/resilience concern in craqly-clone backend or renderer

## Prerequisites

- Project root has `backend/`, `frontend/`, `renderer.js`, `tests/`
- Key modules: `backend/resilient_ocr.py`, `backend/resilient_llm.py`, `backend/fallback.py`, `backend/answer_cache.py`
- Test file: `tests/test_resilience.py`
- Dev-skills plugins loaded (dev-fix, dev-verify)
- Staff-engineer-mode plugin loaded (dependency-resilience, llm-serving-cost-and-latency, production-readiness-review, observability-and-alerting)

## Workflow

### Step 1 — Triage & Capture Symptom

Capture from user screenshot/description:
- **Symptom**: OCR empty / LLM slow / WS disconnect
- **Expected**: What should happen instead
- **Severity**: functional / blocker / minor
- **Repro path**: Which endpoint/entry triggered it

### Step 2 — Specialise Routing

Based on symptom:
- OCR empty → **dependency-resilience** (dependency failure policy)
- LLM slow/first-token timeout → **llm-serving-cost-and-latency** (serving budgets)
- WS disconnect → **persistent-connection-systems** (reconnect/backoff)
- Always pair with **production-readiness-review** for go/no-go

### Step 3 — Reproduce with Failing Test

Write 1-3 regression tests before any code change:
```python
# tests/test_resilience.py
class TestResilientOCR:
    def test_backend_none_emits_install_hint(self):
        """backend=='none' → hint 含 pip install 命令 + 3 条兜底"""
    def test_short_text_passes_or_distinguishes_short_hint(self):
        """1-2 字符文本 → 放行或给出 short hint"""
    def test_preprocess_exception_does_not_silently_drop(self):
        """preprocess_image 异常 → errors 字段记录 + hint 标注增强失败"""
```
**Rule**: 3/3 must FAIL before any fix work begins.

### Step 4 — Hypothesize (No Guessing)

List 3-5 hypotheses across different dimensions:
```
H1: source mapping — recognize_with_fallback 不把 final_fallback 映射为 "empty"
H2: validate threshold — _validate_ocr 硬编码 len>=3 无 min_chars 参数
H3: errors field missing — FallbackResult 无 errors 字段，增强层异常不外传
H4: entry coverage — server.py HTTP 入口没走降级 / /api/ocr/recognize 入参不兼容
H5: frontend gap — renderer.js 不消费 source/hint/backend/total_ms 字段
```

### Step 5 — Surgical Fix

**Only modify root-cause paths:**
1. `backend/fallback.py` — add `errors: list[str]` to FallbackResult
2. `backend/resilient_ocr.py` — 4-tier hint (none_backend/short/enhance_err/empty), `min_chars` param, source mapping
3. `backend/server.py` — all OCR routes use `recognize_with_fallback`, `/api/ocr/recognize` accepts multipart + JSON b64
4. `renderer.js` — `applyOcrResult()` helper, 3 entry points (clipboard/file blob/WS) all call it

### Step 6 — Verify (Red-Green-Red)

1. **GREEN**: `pytest tests/test_resilience.py::TestResilientOCR -v` → 3/3 pass
2. **REVERSE**: Temporary revert source mapping + hint generation → 3/3 FAIL (reverse proof)
3. **WIDER**: `pytest tests/test_resilience.py tests/test_ocr_optimization.py tests/test_server.py -q` → 53/53 pass
4. **FULL**: `pytest tests/ --ignore=tests/test_latency_e2e.py ...` → 0 new regressions

### Step 7 — SEM Deliverables

Produce:
1. **PRR local-only readiness matrix** (6-domain status + blockers/exceptions/follow-ups)
2. **Observability dashboard spec** (4 rows: SLO lights / latency / fallbacks / cache)
3. **Alert policy** (urgent/follow-up/diagnostic with runbook per alert)
4. **Architecture component map + dependency matrix**
5. **Per-hop timeout budget table** (OCR/LLM/WS/ASR)
6. **dev-fix artifact** → `.claude/artifacts/fixes/<slug>.md`

### Step 8 — Dev-Fix Artifact

Write artifact with template:
- Symptom / Expected / Reproduction
- Hypotheses table with Verdict + Evidence
- Root cause (2-3 sentence causal chain)
- Fix (file list + diff summary)
- Verification (V-1 GREEN / V-2 RED reverse / V-3 wider suite / V-4 full suite)
- Regression test path + name
- Pattern analysis (grep repo for same pattern)
- Open questions / Follow-ups

## Code Conventions

- **外科手术式改动**: Only touch root-cause paths, never refactor adjacent code
- **validate 可调**: `min_chars` parameter on `_validate_ocr` (default 3)
- **errors 必须外传**: Every FallbackResult carries `errors: list[str]`
- **hint 分档**: none_backend / short / enhance_err / empty_normal — 4 distinct user-visible messages
- **source 映射**: internal `final_fallback` → user-visible `empty`; never expose internal names
- **Py39 compatible**: Use `Optional[X]` not `X | None`

## SLO Acceptance

| Metric | Target |
|---|---|
| P50 first-token latency | < 500ms |
| P99 first-token latency | < 1000ms |
| OCR auto-recovery rate | > 95% |
| LLM auto-degradation rate | > 99% |
| WS auto-reconnect rate | > 99% |

All 5 indicators are exposed via `/api/metrics` → `acceptance` dict with boolean values.

## Anti-Patterns to Avoid

- ❌ Silently swallowing OCR empty results without hint
- ❌ Hardcoding `len>=3` validate threshold without parameter
- ❌ Exposing internal fallback names (final_fallback) to users
- ❌ Only fixing one entry point (WS screenshot) while leaving HTTP routes unpatched
- ❌ Testing fix without reverse-proofing (stash → RED)
- ❌ Mixing refactor into a surgical fix
- ❌ Skipping errors field on FallbackResult
