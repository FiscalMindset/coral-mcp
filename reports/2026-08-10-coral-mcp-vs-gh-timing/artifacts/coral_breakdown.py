import json, subprocess, time, select

QUERY = "SELECT name, head_branch, status, conclusion, created_at, updated_at, run_number FROM github.repo_action_runs WHERE owner='FiscalMindset' AND repo='coral' AND status IN ('queued','in_progress','waiting','requested') ORDER BY created_at DESC LIMIT 5"
TASK_ID = "3ac9fa5d-ca1c-44c0-8453-b7adc838541f"

proc = subprocess.Popen(["coral","mcp-stdio"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=open("/tmp/coral_breakdown.log","w"), text=True, bufsize=1)
def send(o): proc.stdin.write(json.dumps(o)+"\n"); proc.stdin.flush()
def read_response(eid, timeout=150):
    deadline=time.time()+timeout
    while True:
        rem=deadline-time.time()
        if rem<=0: raise TimeoutError()
        r,_,_=select.select([proc.stdout],[],[],min(5,rem))
        if not r: continue
        ln=proc.stdout.readline()
        if not ln: continue
        try: o=json.loads(ln)
        except: continue
        if o.get("id")==eid: return o

t0=time.time()
send({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"bd","version":"1.0"}}})
read_response(1)
t1=time.time()
send({"jsonrpc":"2.0","method":"notifications/initialized","params":{}})
send({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"sql","arguments":{"queries":[QUERY],"intent":"breakdown","task_id":TASK_ID}}})
read_response(2)
t2=time.time()
print("phase1_initialize_mcp: %.2fs" % (t1-t0))
print("phase2_sql_query:      %.2fs" % (t2-t1))
print("TOTAL:                 %.2fs" % (t2-t0))
proc.kill()
