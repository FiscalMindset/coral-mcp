import json, subprocess, time, select, sys

QUERY = sys.argv[1]
TASK_ID = "e4cf43a1-a3d0-4a17-8273-41bbc33ce3c6"
LOG = sys.argv[2]

proc = subprocess.Popen(["coral","mcp-stdio"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=open(LOG,"w"), text=True, bufsize=1)
def send(o): proc.stdin.write(json.dumps(o)+"\n"); proc.stdin.flush()
def read_response(eid, timeout=200):
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
send({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"diag","version":"1.0"}}})
read_response(1)
t1=time.time()
send({"jsonrpc":"2.0","method":"notifications/initialized","params":{}})
send({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"sql","arguments":{"queries":[QUERY],"intent":"diag","task_id":TASK_ID}}})
resp=read_response(2)
t2=time.time()
res=resp.get("result",{})
sc=res.get("structuredContent",{})
rows = sc.get("results",[{}])[0].get("rows",[]) if sc.get("results") else []
print("init: %.2fs | sql: %.2fs | TOTAL: %.2fs" % (t1-t0, t2-t1, t2-t0))
print("isError:", res.get("isError"), "| rows_returned:", len(rows))
for r in rows[:3]:
    print("ROW:", json.dumps(r)[:180])
proc.kill()
