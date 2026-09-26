# AegisOps — Autonomous Incident Diagnosis & Safe Remediation

A hackathon-ready, local-first Agentic SRE platform. It simulates production telemetry, correlates logs/metrics/traces/deployments, generates evidence-backed hypotheses, tests them, recommends a safe remediation, gates risky actions behind approval, executes in a sandbox, verifies recovery, and records an audit trail.

## 60-second demo
1. `python -m venv .venv && source .venv/bin/activate` (Windows: `.venv\Scripts\activate`)
2. `pip install -r requirements.txt`
3. `python -m uvicorn backend.main:app --reload --port 8000`
4. Open `http://localhost:8000`
5. Click **Run Incident Replay**.
6. Watch the agents build a timeline, score hypotheses, test counterfactuals, run the sandbox, and request approval.
7. Click **Approve & Execute** and watch verification / rollback protection.
8. Open **Benchmark** to run labeled scenarios.

No API key is required. The reasoning engine is deterministic-first so the demo is reliable offline. An optional Azure OpenAI adapter can be added later without changing the core contracts.

## Architecture
Frontend (single-page dashboard) → FastAPI → Incident Orchestrator → specialized agents → evidence/scoring engine → sandbox remediation → approval gate → verification → audit store.

## Scenarios
- bad_deployment
- db_pool_exhaustion
- memory_leak
- dependency_timeout
- traffic_spike

## Safety
The demo never touches a real cloud account. Production-like actions are represented as sandbox state transitions. Risky actions require explicit approval. Every action is immutable in the audit log, and failed verification triggers rollback.

## Microsoft alignment
Designed around patterns demonstrated by Azure SRE Agent / Azure Monitor Observability Agent: cross-signal investigation, topology-aware correlation, governed automation, approvals, and persistent incident context.
