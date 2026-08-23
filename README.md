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

## Key Modules

| File | Purpose |
|---|---|
| `backend/fallback.py` | Timeout circuit breaker + serial degradation + parallel race + FallbackStats |
| `backend/resilient_ocr.py` | OCR 3-level fallback (primary→enhanced→cache) with 4-tier hint |
| `backend/resilient_llm.py` | LLM parallel primary/fast model race + template fallback |
| `backend/resilient_asr.py` | ASR engine switch chain (Paraformer→Whisper→empty) |
| `backend/answer_cache.py` | 3-level answer cache (memory LRU→JSON file→Hot 100 preload) |
| `frontend/src/composables/useWebSocket.ts` | Exponential backoff + pending message cache |

## SLO Acceptance

| Metric | Target |
|---|---|
| P50 first-token latency | < 500ms |
| P99 first-token latency | < 1000ms |
| OCR auto-recovery rate | > 95% |
| LLM auto-degradation rate | > 99% |
| WS auto-reconnect rate | > 99% |

All 5 indicators exposed via `GET /api/metrics` → `acceptance` dict.

## License

MIT
