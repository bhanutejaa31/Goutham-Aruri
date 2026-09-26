from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from backend.orchestrator import Orchestrator
from backend.models import ApprovalRequest

app = FastAPI(title="AegisOps", version="1.0")
orch = Orchestrator()

app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def index():
    return FileResponse("frontend/index.html")

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "aegisops"}

@app.get("/api/scenarios")
def scenarios():
    return orch.list_scenarios()

@app.post("/api/incidents/{scenario}/replay")
def replay(scenario: str):
    return orch.run_investigation(scenario)

@app.get("/api/incidents/{incident_id}")
def get_incident(incident_id: str):
    return orch.get_incident(incident_id)

@app.post("/api/incidents/{incident_id}/approve")
def approve(incident_id: str, req: ApprovalRequest):
    return orch.approve_and_execute(incident_id, req.approved)

@app.post("/api/benchmark")
def benchmark():
    return orch.benchmark()
