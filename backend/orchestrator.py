import json, os, uuid, time
from backend.scenarios import SCENARIOS, make_events
from backend.agents import LogAgent,MetricAgent,TraceAgent,ChangeAgent,DependencyAgent,CausalAgent,EvidenceGate,RemediationAgent,VerificationAgent

class Orchestrator:
    def __init__(self):
        self.incidents={}
        os.makedirs("data",exist_ok=True)
        self.audit_path=os.path.join("data","audit.jsonl")
        self.agents=[LogAgent(),MetricAgent(),TraceAgent(),ChangeAgent(),DependencyAgent()]
        self.causal=CausalAgent(); self.gate=EvidenceGate()
        self.remediator=RemediationAgent(); self.verifier=VerificationAgent()

    def audit(self, incident_id, action, details):
        rec={"timestamp":time.time(),"incident_id":incident_id,"action":action,"details":details}
        self.incidents[incident_id]["audit"].append(rec)
        with open(self.audit_path,"a",encoding="utf-8") as f: f.write(json.dumps(rec)+"\n")

    def list_scenarios(self):
        return [{"id":k,"title":v["title"],"root":v["root"]} for k,v in SCENARIOS.items()]

    def run_investigation(self, scenario):
        if scenario not in SCENARIOS: return {"error":"unknown scenario"}
        iid="INC-"+uuid.uuid4().hex[:8].upper()
        events=make_events(scenario)
        evidence={}
        for a in self.agents:
            evidence[a.__class__.__name__]=a.run(events)
        timeline=sorted([{"timestamp":e["timestamp"],"service":e["service"],"kind":e["kind"],"message":e["message"]} for e in events],key=lambda x:x["timestamp"])
        hypotheses=self.causal.run(scenario,events,evidence)
        gate=self.gate.evaluate(hypotheses)
        top=hypotheses[0]
        remediation=self.remediator.plan(scenario,top["id"][2:],sandbox=True)
        inc={"id":iid,"scenario":scenario,"title":SCENARIOS[scenario]["title"],"severity":"CRITICAL",
             "status":"AWAITING_APPROVAL" if gate["sufficient"] else "NEEDS_DATA",
             "events":events,"hypotheses":hypotheses,"root_cause":top["id"][2:],
             "confidence":top["confidence"],"remediation":remediation,"audit":[],"timeline":timeline,
             "evidence":evidence,"gate":gate,"verification":None}
        self.incidents[iid]=inc
        self.audit(iid,"INVESTIGATION_COMPLETED",{"root_cause":inc["root_cause"],"confidence":inc["confidence"],"evidence_gate":gate})
        return inc

    def get_incident(self,iid):
        return self.incidents.get(iid,{"error":"not found"})

    def approve_and_execute(self,iid,approved):
        if iid not in self.incidents: return {"error":"not found"}
        inc=self.incidents[iid]
        if inc["status"] not in ("AWAITING_APPROVAL","NEEDS_DATA"):
            return {"error":f"Incident already in terminal state: {inc['status']}"}
        if not approved:
            inc["status"]="REJECTED"
            self.audit(iid,"REMEDIATION_REJECTED",{})
            return inc
        if not inc["gate"]["sufficient"]:
            return {"error":"Approval blocked: evidence gate failed."}
        self.audit(iid,"HUMAN_APPROVAL",{"approved":True,"risk":inc["remediation"]["risk"]})
        self.audit(iid,"SANDBOX_EXECUTION",{"action":inc["remediation"]["action"],"target":inc["remediation"]["target"]})
        ver=self.verifier.verify(inc["scenario"],inc["remediation"])
        inc["verification"]=ver
        if ver["success"]:
            inc["status"]="RESOLVED"
            self.audit(iid,"VERIFICATION_PASSED",ver)
            self.audit(iid,"REMEDIATION_EXECUTED",{"sandbox":True,"production_simulation":True})
        else:
            inc["status"]="ROLLED_BACK"
            self.audit(iid,"ROLLBACK",{"reason":"verification failed"})
        return inc

    def benchmark(self):
        rows=[]
        for s in SCENARIOS:
            inc=self.run_investigation(s)
            correct=inc["root_cause"]==SCENARIOS[s]["root"]
            rows.append({"scenario":s,"predicted":inc["root_cause"],"truth":SCENARIOS[s]["root"],"correct":correct,
                         "confidence":inc["confidence"]})
        acc=sum(r["correct"] for r in rows)/len(rows)
        return {"accuracy":round(acc,3),"scenarios":rows,"note":"Synthetic labeled benchmark; run results are local demo measurements."}
