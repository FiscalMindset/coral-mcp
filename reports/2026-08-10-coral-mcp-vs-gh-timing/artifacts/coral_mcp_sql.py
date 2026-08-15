import json, subprocess, time, select

QUERY = "SELECT name, head_branch, status, conclusion, created_at, updated_at, run_number FROM github.repo_action_runs WHERE owner='FiscalMindset' AND repo='coral' AND status IN ('queued','in_progress','waiting','requested') ORDER BY created_at DESC LIMIT 5"
TASK_ID = "13e7e0ae-7e83-4388-906c-44821ef48286"

proc = subprocess.Popen(["coral", "mcp-stdio"],
                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL, text=True, bufsize=1)

def send(obj):
    proc.stdin.write(json.dumps(obj) + "\n")
    proc.stdin.flush()

def read_response(expected_id, timeout=150):
    deadline = time.time() + timeout
    while True:
        remaining = deadline - time.time()
        if remaining <= 0:
            raise TimeoutError("no response id=%s" % expected_id)
        r, _, _ = select.select([proc.stdout], [], [], min(5, remaining))
        if not r:
            continue
        line = proc.stdout.readline()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if obj.get("id") == expected_id:
            return obj

t0 = time.time()
send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
      "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                 "clientInfo": {"name": "timing-test", "version": "1.0"}}})
read_response(1)
send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
send({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
      "params": {"name": "sql",
                 "arguments": {"queries": [QUERY], "intent": "timing comparison", "task_id": TASK_ID}}})
resp = read_response(2)
elapsed = round(time.time() - t0, 3)
result = resp.get("result", {})
is_err = result.get("isError", False)
content = result.get("content", [])
text = "".join(c.get("text", "") for c in content if c.get("type") == "text")
print("elapsed_seconds:", elapsed)
print("isError:", is_err)
print("raw_result:", json.dumps(result)[:3000])
proc.kill()
