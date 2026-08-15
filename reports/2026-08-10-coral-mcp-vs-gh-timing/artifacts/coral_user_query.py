import json, subprocess, time, select, sys

QUERY = sys.argv[1]
TASK_ID = sys.argv[2] if len(sys.argv) > 2 else "9fb7d5b2-ca35-4233-8ee1-5f9e45e659f5"
LOG = sys.argv[3] if len(sys.argv) > 3 else "/tmp/coral_user_query.log"

proc = subprocess.Popen(["coral", "mcp-stdio"],
                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=open(LOG, "w"), text=True, bufsize=1)

def send(o):
    proc.stdin.write(json.dumps(o) + "\n")
    proc.stdin.flush()

def read_response(eid, timeout=240):
    deadline = time.time() + timeout
    while True:
        rem = deadline - time.time()
        if rem <= 0:
            raise TimeoutError("no response id=%s" % eid)
        r, _, _ = select.select([proc.stdout], [], [], min(5, rem))
        if not r:
            continue
        ln = proc.stdout.readline()
        if not ln:
            continue
        try:
            o = json.loads(ln)
        except Exception:
            continue
        if o.get("id") == eid:
            return o

t0 = time.time()
send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
      "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                 "clientInfo": {"name": "user-query-harness", "version": "1.0"}}})
read_response(1)
t1 = time.time()
send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
send({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
      "params": {"name": "sql",
                 "arguments": {"queries": [QUERY], "intent": "user real query benchmark", "task_id": TASK_ID}}})
resp = read_response(2)
t2 = time.time()
res = resp.get("result", {})
sc = res.get("structuredContent", {})
results = sc.get("results", []) if sc else []
rows = results[0].get("rows", []) if results else []
cols = results[0].get("columns", []) if results else []
print("init: %.2fs | sql: %.2fs | TOTAL: %.2fs" % (t1 - t0, t2 - t1, t2 - t0))
print("isError:", res.get("isError"))
print("columns:", cols)
print("rows_returned:", len(rows))
for r in rows:
    print("ROW:", json.dumps(r)[:600])
proc.kill()
