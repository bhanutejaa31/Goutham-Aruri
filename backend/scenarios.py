import time, uuid

BASE = 1700000000.0

SCENARIOS = {
 "bad_deployment": {
   "title": "Checkout regression after deployment",
   "root": "bad_deployment",
   "remediation": {"action":"rollback", "target":"checkout-service", "risk":"HIGH",
                   "description":"Rollback checkout-service to the last known-good release."},
   "events": [
    (0,"deployment","checkout-service","Deployment v2.4.1 completed","info",None,None),
    (12,"metric","checkout-service","p95 latency increased to 820ms","warning",820,None),
    (17,"log","checkout-service","ERROR NullReferenceError in pricing path","error",None,"tr-101"),
    (20,"trace","api-gateway","checkout span duration 1.9s","warning",1900,"tr-101"),
    (24,"metric","checkout-service","error rate increased to 31%","error",31,None),
    (27,"log","api-gateway","upstream checkout timeout","error",None,"tr-101"),
   ]
 },
 "db_pool_exhaustion": {
   "title": "Checkout outage from database pool exhaustion",
   "root": "db_pool_exhaustion",
   "remediation": {"action":"restart", "target":"order-service", "risk":"HIGH",
                   "description":"Recycle order-service workers to release exhausted DB connections."},
   "events": [
    (0,"metric","postgres","connection pool utilization 99%","error",99,None),
    (5,"metric","postgres","p95 query latency 640ms","error",640,None),
    (9,"trace","order-service","DB span wait 580ms","warning",580,"tr-202"),
    (13,"log","order-service","ERROR connection pool timeout","error",None,"tr-202"),
    (18,"metric","order-service","API error rate 28%","error",28,None),
    (22,"log","api-gateway","504 from order-service","error",None,"tr-202"),
   ]
 },
 "memory_leak": {
   "title": "Memory leak causing worker restarts",
   "root": "memory_leak",
   "remediation": {"action":"rollback", "target":"catalog-service", "risk":"HIGH",
                   "description":"Rollback the recent catalog release suspected of leaking memory."},
   "events": [
    (0,"deployment","catalog-service","Deployment v5.7.0 completed","info",None,None),
    (10,"metric","catalog-service","memory 72%","warning",72,None),
    (22,"metric","catalog-service","memory 91%","warning",91,None),
    (29,"log","catalog-service","GC pause time exceeded 900ms","warning",900,None),
    (36,"metric","catalog-service","memory 99%","error",99,None),
    (41,"log","catalog-service","OOMKilled; container restarted","error",None,None),
   ]
 },
 "dependency_timeout": {
   "title": "Payment dependency timeout",
   "root": "dependency_timeout",
   "remediation": {"action":"circuit_break", "target":"payment-client", "risk":"MEDIUM",
                   "description":"Enable the payment-client circuit breaker and reduce retry amplification."},
   "events": [
    (0,"metric","payment-api","dependency latency 2100ms","error",2100,None),
    (8,"trace","payment-service","external payment span timeout","error",2000,"tr-404"),
    (14,"log","payment-service","retry budget exceeded","error",None,"tr-404"),
    (20,"metric","payment-service","thread utilization 97%","error",97,None),
    (26,"metric","checkout-service","checkout errors 19%","error",19,None),
   ]
 },
 "traffic_spike": {
   "title": "Traffic surge saturating checkout",
   "root": "traffic_spike",
   "remediation": {"action":"scale", "target":"checkout-service", "risk":"MEDIUM",
                   "description":"Increase checkout-service replicas from 3 to 6."},
   "events": [
    (0,"metric","gateway","request rate 3.2x baseline","warning",320,None),
    (6,"metric","checkout-service","CPU 94%","error",94,None),
    (12,"metric","checkout-service","queue depth 840","error",840,None),
    (18,"trace","checkout-service","request duration 1500ms","warning",1500,"tr-505"),
    (24,"metric","checkout-service","error rate 14%","error",14,None),
   ]
 }
}

def make_events(scenario):
    events=[]
    for i,(offset,kind,service,msg,severity,value,trace) in enumerate(SCENARIOS[scenario]["events"]):
        events.append({
            "id": f"E-{scenario[:3].upper()}-{i+1:02d}",
            "timestamp": BASE+offset,
            "service": service, "kind":kind, "message":msg,
            "severity":severity, "value":value, "trace_id":trace,
            "metadata": {}
        })
    return events
