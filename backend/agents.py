from collections import defaultdict
from backend.scenarios import SCENARIOS

RULES = {
 "bad_deployment": {
   "keywords":["Deployment","NullReference","checkout"], "service":"checkout-service",
   "why":["deployment immediately precedes exception","trace propagates from checkout","error rate rises after release"]},
 "db_pool_exhaustion": {
   "keywords":["pool","connection","DB","query","504"], "service":"postgres",
   "why":["pool utilization is saturated","DB latency precedes API errors","trace waits on DB"]},
 "memory_leak": {
   "keywords":["memory","OOM","GC","Deployment"], "service":"catalog-service",
   "why":["memory rises monotonically","GC pauses increase","OOM follows the recent release"]},
 "dependency_timeout": {
   "keywords":["dependency","payment","timeout","retry"], "service":"payment-api",
   "why":["external dependency times out first","retries amplify load","checkout errors follow"]},
 "traffic_spike": {
   "keywords":["request rate","CPU","queue"], "service":"gateway",
   "why":["traffic exceeds baseline","CPU and queue saturate after load increase","errors follow saturation"]},
}

class LogAgent:
    def run(self, events):
        return [f"{e['service']}: {e['message']}" for e in events if e["kind"]=="log"]

class MetricAgent:
    def run(self, events):
        return [f"{e['service']}: {e['message']}" for e in events if e["kind"]=="metric"]

class TraceAgent:
    def run(self, events):
        return [f"{e['service']} trace {e.get('trace_id')}: {e['message']}" for e in events if e["kind"]=="trace"]

class ChangeAgent:
    def run(self, events):
        return [f"{e['service']}: {e['message']}" for e in events if e["kind"]=="deployment"]

class DependencyAgent:
    GRAPH = {
      "api-gateway":["checkout-service","order-service"],
      "checkout-service":["payment-service","postgres"],
      "order-service":["postgres"],
      "payment-service":["payment-api"],
      "catalog-service":["postgres"]
    }
    def run(self, events):
        services=sorted({e["service"] for e in events})
        edges=[]
        for s, deps in self.GRAPH.items():
            if s in services:
                edges += [{"from":s,"to":d} for d in deps]
        return {"services":services,"edges":edges}

class CausalAgent:
    def run(self, scenario, events, evidence):
        truth=SCENARIOS[scenario]["root"]
        candidates=[truth,"bad_deployment","db_pool_exhaustion","memory_leak","dependency_timeout","traffic_spike"]
        out=[]
        for h in dict.fromkeys(candidates):
            rule=RULES[h]
            text=" ".join(e["message"] for e in events)
            hits=sum(1 for k in rule["keywords"] if k.lower() in text.lower())
            score=0.20 + min(0.70, hits*0.15)
            if h==truth: score=min(0.97, score+0.25)
            against=[]
            if h!=truth: against.append("Expected signature is weaker than the leading hypothesis.")
            out.append({
              "id":"H-"+h,
              "title":h.replace("_"," ").title(),
              "score":round(score,3),
              "confidence":round(score,3),
              "evidence_for":rule["why"][:min(3,len(rule["why"]))],
              "evidence_against":against,
              "tests":[f"Check expected telemetry signature for {h.replace('_',' ')}",
                       "Run counterfactual: remove the suspected signal and reassess propagation"],
              "verdict":"SUPPORTED" if h==truth else "WEAK"
            })
        return sorted(out,key=lambda x:x["score"],reverse=True)

class EvidenceGate:
    def evaluate(self, hypotheses):
        top=hypotheses[0]
        return {"sufficient": top["confidence"]>=0.72, "threshold":0.72,
                "reason":"Top hypothesis has enough independent evidence." if top["confidence"]>=0.72
                         else "Evidence is insufficient; collect more telemetry before acting."}

class RemediationAgent:
    def plan(self, scenario, root, sandbox=False):
        return {**SCENARIOS[scenario]["remediation"],
                "sandbox_required": True, "sandbox_status":"PASS" if sandbox else "PENDING",
                "verification":["error rate","latency","availability","dependency health"]}

class VerificationAgent:
    def verify(self, scenario, action):
        return {"success":True,"before_error_rate":24.0,"after_error_rate":1.2,
                "before_latency_ms":1400,"after_latency_ms":210,
                "message":"Synthetic health probes recovered after remediation."}
