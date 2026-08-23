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
- Taxonomy module: `backend/skill_taxonomy.py` (分类注册表)
- Test files: `tests/test_resilience.py`, `tests/test_skill_taxonomy.py`
- Dev-skills plugins loaded (dev-fix, dev-verify)
- Staff-engineer-mode plugin loaded (dependency-resilience, llm-serving-cost-and-latency, production-readiness-review, observability-and-alerting)

## Detailed Classification System

### 三大场景二级分类 (15 子类)

Skill 通过 `backend/skill_taxonomy.py` 提供**关键词驱动的自动分类**，用户描述会被路由到具体子类，从而触发精准的修复策略。

#### OCR 场景 (6 子类)

| 子类 ID | 触发关键词 | 关联代码路径 |
|---|---|---|
| `backend_none` | OCR 后端加载失败、RapidOCR/PaddleOCR 不可用 | `backend/resilient_ocr.py::_check_ocr_available` |
| `preprocess_failure` | 图片预处理异常、preprocess_image 抛异常 | `backend/screenshot.py::preprocess_image` |
| `empty_output` | OCR 引擎正常但返回空字符串 | `backend/resilient_ocr.py::_validate_ocr` |
| `short_text` | 识别结果 1-2 字符、文本过短 | `backend/resilient_ocr.py::_validate_ocr` |
| `low_contrast` | 图片对比度低、文字模糊 | `backend/screenshot.py::preprocess_image` |
| `code_mojibake` | 代码符号混淆 O/0、l/1 | `backend/ocr_post_process.py::fix_code_symbols` |

#### LLM 场景 (5 子类)

| 子类 ID | 触发关键词 | 关联代码路径 |
|---|---|---|
| `first_token_timeout` | 首 token 超时、思考中卡死 | `backend/resilient_llm.py::chat_stream_with_budget` |
| `full_timeout` | 完整响应超时、流式中断 | `backend/resilient_llm.py::chat_stream_with_budget` |
| `degradation_failure` | 降级策略失效、并行主备都失败 | `backend/resilient_llm.py::parallel_with_template` |
| `cache_miss_fallback` | 高频题库缓存未命中、兜底失效 | `backend/answer_cache.py::AnswerCache` |
| `token_overrun` | token 超限、max_tokens 截断 | `config.py::llm_max_tokens` |

#### WS 场景 (4 子类)

| 子类 ID | 触发关键词 | 关联代码路径 |
|---|---|---|
| `initial_connect_fail` | 首次连接失败、未连接 | `renderer.js::connectWebSocket` |
| `disconnect_timeout` | 超时断开、心跳丢失 | `renderer.js::wsHeartbeat` |
| `reconnect_exhausted` | 重连次数耗尽、退避到最大值 | `renderer.js::reconnectWS` |
| `message_ordering` | 消息顺序错乱、chunk 乱序 | `renderer.js::handleWsMessage` |

### Anti-Pattern 严重程度分类

| 严重程度 | 反模式 ID | 说明 |
|---|---|---|
| **critical** | `silently_swallow_error` | 静默吞没错误，用户完全无感 |
| **critical** | `no_hint_on_empty` | 空结果无任何提示 |
| **high** | `single_entry_fix` | 只修单入口，其他入口仍有 bug |
| **high** | `mix_refactor_in_fix` | 修复中夹带无关重构 |
| **high** | `skip_reverse_proof` | 跳过反向验证，无法证明 fix 有效 |
| **medium** | `hardcoded_threshold` | 硬编码阈值（如 len>=3） |
| **medium** | `missing_errors_field` | FallbackResult 缺少 errors 字段 |
| **low** | `expose_internal_name` | 暴露内部名称给用户 |
| **low** | `missing_code_convention` | 不遵循代码约定 |

### SLO 指标检查阶段分类

| 检查阶段 | 指标 ID | 触发关键词 |
|---|---|---|
| **pre_merge** | `p50_latency` | P50 首 token 延迟 |
| **pre_merge** | `p99_latency` | P99 首 token 延迟 |
| **post_deploy** | `auto_recovery_rate` | OCR 自动恢复率 |
| **post_deploy** | `auto_degradation_rate` | LLM 自动降级率 |
| **monitoring** | `reconnect_rate` | WS 自动重连率 |
| **monitoring** | `first_token_p99` | 首 token P99 监控 |

### Workflow Step 子任务分类

| Step ID | 阶段 | 子任务 | 产出物 |
|---|---|---|---|
| `triage` | triage | symptom capture, expected, severity, repro path | 症状描述文档 |
| `routing` | triage | specialist selection, PRR pairing | 路由决策记录 |
| `reproduce` | reproduce | write test, verify FAIL, capture error | Failing test + 错误日志 |
| `hypothesize` | hypothesize | list 3-5 hypotheses, rank, select primary | 假设列表 + 优先级 |
| `fix` | fix | identify paths, apply fix, update routes | 代码 diff |
| `verify` | verify | GREEN → REVERSE → WIDER → FULL | 验证证据链 |
| `sem_deliverables` | deliver | PRR matrix, observability spec, alert policy | 6 项交付物 |
| `dev_fix_artifact` | deliver | 8 个 artifact section | 完整修复记录 |

### 分类注册表验证

```python
# 校验分类体系完整性
from backend.skill_taxonomy import validate_skill_taxonomy

result = validate_skill_taxonomy()
assert result.valid is True, f"分类冲突: {result.errors}"

# 单元测试
pytest tests/test_skill_taxonomy.py -v  # 42 个测试全通过
```

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
