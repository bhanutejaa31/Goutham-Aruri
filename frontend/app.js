let current=null;

async function loadScenarios(){
 const r=await fetch('/api/scenarios'); const data=await r.json();
 document.getElementById('scenarios').innerHTML=data.map(s=>`<div class="scenario" onclick="runReplay('${s.id}')"><b>${s.title}</b><span>${s.id}</span></div>`).join('');
}
async function runReplay(scenario){
 scenario=scenario||'bad_deployment';
 document.getElementById('empty').style.display='none';
 document.getElementById('dashboard').style.display='block';
 document.getElementById('incTitle').innerText='Investigating...';
 const r=await fetch('/api/incidents/'+scenario+'/replay',{method:'POST'}); current=await r.json(); render();
}
function render(){
 const x=current;
 document.getElementById('incTitle').innerText=x.title;
 document.getElementById('incId').innerText=x.id+' · '+x.scenario;
 document.getElementById('status').innerText=x.status.replaceAll('_',' ');
 document.getElementById('status').className='pill '+(x.status==='RESOLVED'?'green':'');
 document.getElementById('confidence').innerText=Math.round(x.confidence*100)+'%';
 document.getElementById('events').innerText=x.events.length;
 document.getElementById('agentCount').innerText=Object.keys(x.evidence).length+4; // +Causal, EvidenceGate, Remediation, Verification agents
 document.getElementById('risk').innerText=x.remediation.risk;
 document.getElementById('rootCause').innerText='ROOT CAUSE → '+x.root_cause.replaceAll('_',' ').toUpperCase();

 document.getElementById('hypotheses').innerHTML=x.hypotheses.map((h,i)=>`
 <div class="hyp ${i===0?'top':''}">
   <b>${i+1}. ${h.title}</b> <span class="pill">${Math.round(h.confidence*100)}%</span>
   <div class="bar"><div class="fill" style="width:${Math.round(h.confidence*100)}%"></div></div>
   <div class="evidence">✓ ${h.evidence_for.join(' · ')}</div>
   ${h.evidence_against.length?'<div class="evidence">✗ '+h.evidence_against.join(' · ')+'</div>':''}
 </div>`).join('');

 document.getElementById('timeline').innerHTML=x.timeline.map(e=>`<div class="event"><b>${e.service} · ${e.kind}</b><div>${e.message}</div></div>`).join('');

 let edges=(x.evidence.DependencyAgent||{}).edges||[];
 document.getElementById('graph').innerHTML=edges.length
   ? edges.map(e=>`<span class="node">${e.from}</span><span class="arrow">→</span><span class="node">${e.to}</span>`).join('')
   : '<span class="evidence">No dependency edges observed for this incident.</span>';

 document.getElementById('remediation').innerHTML=`
 <b>${x.remediation.action.toUpperCase()}</b> → ${x.remediation.target}<br>
 <span class="evidence">${x.remediation.description}</span><br><br>
 <span class="pill">🧪 SANDBOX ${x.remediation.sandbox_status}</span>
 <span class="pill">⚠ ${x.remediation.risk} RISK</span>
 <p>Verification: ${x.remediation.verification.join(', ')}</p>`;
 if(x.status==='AWAITING_APPROVAL'){
   document.getElementById('approval').innerHTML=`<hr><b>Human approval required for risky action.</b><br><br>
   <button class="approve" onclick="approve(true)">✓ Approve & Execute</button>
   <button class="reject" onclick="approve(false)">Reject</button>`;
 } else if(x.status==='REJECTED'){
   document.getElementById('approval').innerHTML=`<hr><b>✗ Remediation rejected. No action was taken.</b>`;
 } else if(x.verification){
   document.getElementById('approval').innerHTML=`<hr><b>✓ ${x.verification.message}</b><br>Error rate: ${x.verification.before_error_rate}% → ${x.verification.after_error_rate}% · Latency: ${x.verification.before_latency_ms}ms → ${x.verification.after_latency_ms}ms`;
 } else {
   document.getElementById('approval').innerHTML=`<hr><b>${x.gate.reason}</b>`;
 }
 document.getElementById('audit').innerHTML=x.audit.map(a=>`<div><b>${a.action}</b> — ${JSON.stringify(a.details)}</div>`).join('');
}
async function approve(value){
 const r=await fetch('/api/incidents/'+current.id+'/approve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({approved:value})});
 const result=await r.json();
 if(result.error){ alert(result.error); return; }
 current=result; render();
}
async function runBenchmark(){
 document.getElementById('benchmark').innerHTML='<p>Running...</p>';
 const r=await fetch('/api/benchmark',{method:'POST'}); const x=await r.json();
 document.getElementById('benchmark').innerHTML=`<hr><b>RCA Accuracy: ${Math.round(x.accuracy*100)}%</b><div class="evidence">${x.scenarios.map(s=>`${s.correct?'✓':'✗'} ${s.scenario}`).join('<br>')}</div>`;
}
loadScenarios();
