from pydantic import BaseModel
from typing import Any, Dict, List

class ApprovalRequest(BaseModel):
    approved: bool

class Event(BaseModel):
    id: str
    timestamp: float
    service: str
    kind: str
    message: str
    severity: str = "info"
    trace_id: str | None = None
    value: float | None = None
    metadata: Dict[str, Any] = {}

class Hypothesis(BaseModel):
    id: str
    title: str
    score: float
    confidence: float
    evidence_for: List[str]
    evidence_against: List[str]
    tests: List[str]
    verdict: str

class Incident(BaseModel):
    id: str
    scenario: str
    title: str
    severity: str
    status: str
    events: List[Event]
    hypotheses: List[Hypothesis]
    root_cause: str
    confidence: float
    remediation: Dict[str, Any]
    audit: List[Dict[str, Any]]
    timeline: List[Dict[str, Any]]
    evidence: Dict[str, Any] = {}
    gate: Dict[str, Any] = {}
    verification: Dict[str, Any] | None = None
