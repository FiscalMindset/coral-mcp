"""
Smoke-test driver: runs every probe query in probes.json against coral mcp-stdio,
records status (data / empty / error / timeout), row count, timing, error message.
"""

import json, os, select, subprocess, time, sys

ROOT = "/Users/viclkykumar/code/coral-mcp-benchmark/reports/coral-github-mcp-full-test"
ART = os.path.join(ROOT, "artifacts")
PROBES = json.load(open(os.path.join(ROOT, "probes.json")))["queries"]
TASK_ID = "96ed9317-a1b3-4c4f-8c32-23e5938ff3a6"
INTENT = "smoke-test all 364 github tables"
TIMEOUT_S = 45

def run_one(query, log_path):
    proc = subprocess.Popen(
        ["coral", "mcp-stdio"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=open(log_path, "w"), text=True, bufsize=1,
    )
    def send(o):
        proc.stdin.write(json.dumps(o) + "\n"); proc.stdin.flush()
    def read_response(eid, timeout):
        deadline = time.time() + timeout
        while True:
            rem = deadline - time.time()
            if rem <= 0:
                raise TimeoutError()
            r, _, _ = select.select([proc.stdout], [], [], min(2, rem))
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
    try:
        send({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"smoke","version":"1.0"}}})
        read_response(1, 30)
        send({"jsonrpc":"2.0","method":"notifications/initialized","params":{}})
        send({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"sql","arguments":{"queries":[query],"intent":INTENT,"task_id":TASK_ID}}})
        t0 = time.perf_counter()
        try:
            resp = read_response(2, TIMEOUT_S)
        except TimeoutError:
            elapsed = time.perf_counter() - t0
            proc.kill()
            return {"status": "timeout", "time": round(elapsed, 2), "rows": 0, "error": "no response within %ds" % TIMEOUT_S}
        elapsed = time.perf_counter() - t0
        res = resp.get("result", {})
        if res.get("isError"):
            err_text = ""
            for c in res.get("content", []):
                if c.get("type") == "text":
                    err_text = c.get("text", "")[:400]
                    break
            proc.kill()
            return {"status": "error", "time": round(elapsed, 2), "rows": 0, "error": err_text}
        sc = res.get("structuredContent", {})
        results = sc.get("results", [])
        rows = results[0].get("rows", []) if results else []
        proc.kill()
        return {"status": "data" if len(rows) > 0 else "empty", "time": round(elapsed, 2), "rows": len(rows), "error": None}
    except Exception as e:
        try:
            proc.kill()
        except Exception:
            pass
        return {"status": "crash", "time": 0, "rows": 0, "error": str(e)[:400]}

def main():
    table_list = sorted(PROBES.keys())
    results = {}
    total = len(table_list)
    started = time.time()
    for i, name in enumerate(table_list, 1):
        log = os.path.join(ART, "%s.log" % name)
        r = run_one(PROBES[name], log)
        results[name] = r
        sys.stderr.write("[%d/%d] %-45s %-7s rows=%-4s time=%6.2fs\n" % (
            i, total, name, r["status"], r["rows"], r["time"]))
        sys.stderr.flush()
        if i % 25 == 0:
            tmp = os.path.join(ROOT, "smoke_results.json")
            json.dump(results, open(tmp, "w"), indent=2)
            sys.stderr.write("  [saved checkpoint to smoke_results.json]\n")
    out = os.path.join(ROOT, "smoke_results.json")
    json.dump(results, open(out, "w"), indent=2)
    elapsed = time.time() - started
    counts = {"data":0, "empty":0, "error":0, "timeout":0, "crash":0}
    for r in results.values():
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print("\nDONE in %.0fs" % elapsed)
    print("data=%d  empty=%d  error=%d  timeout=%d  crash=%d" % (
        counts["data"], counts["empty"], counts["error"], counts["timeout"], counts["crash"]))

if __name__ == "__main__":
    main()