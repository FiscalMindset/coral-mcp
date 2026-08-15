import json, os, select, subprocess, time, sys, argparse, resource

def median(vals):
    return sorted(vals)[len(vals) // 2] if vals else float("nan")

def run_gh(cmd, runs):
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    out = []
    for _ in range(runs):
        t0 = time.perf_counter()
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        out.append(time.perf_counter() - t0)
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    return {
        "real_min": round(min(out), 3),
        "real_median": round(median(out), 3),
        "real_max": round(max(out), 3),
        "user": round(after.ru_utime - before.ru_utime, 3),
        "sys": round(after.ru_stime - before.ru_stime, 3),
    }

class WarmCoral:
    def __init__(self, log_path):
        self.proc = subprocess.Popen(
            ["coral", "mcp-stdio"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=open(log_path, "w"), text=True, bufsize=1,
        )
        self._eid = 0
        self._call("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                                  "clientInfo": {"name": "warm-bench", "version": "1.0"}})
    def _send(self, o):
        self.proc.stdin.write(json.dumps(o) + "\n")
        self.proc.stdin.flush()
    def _read(self, eid, timeout=300):
        deadline = time.time() + timeout
        while True:
            rem = deadline - time.time()
            if rem <= 0:
                raise TimeoutError("no response id=%s" % eid)
            r, _, _ = select.select([self.proc.stdout], [], [], min(5, rem))
            if not r:
                continue
            ln = self.proc.stdout.readline()
            if not ln:
                continue
            try:
                o = json.loads(ln)
            except Exception:
                continue
            if o.get("id") == eid:
                return o
    def _call(self, method, params):
        self._eid += 1
        self._send({"jsonrpc": "2.0", "id": self._eid, "method": method, "params": params})
        return self._read(self._eid)
    def initialized(self):
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
    def sql(self, query, task_id, intent="warm-bench"):
        self._eid += 1
        self._send({"jsonrpc": "2.0", "id": self._eid, "method": "tools/call",
                    "params": {"name": "sql",
                               "arguments": {"queries": [query], "intent": intent, "task_id": task_id}}})
        return self._read(self._eid)
    def close(self):
        try:
            self.proc.kill()
        except Exception:
            pass

def run_coral_warm(query, task_id, runs, log_path):
    c = WarmCoral(log_path)
    c.initialized()
    sql_times = []
    rows = 0
    last_resp = None
    for _ in range(runs):
        t0 = time.perf_counter()
        resp = c.sql(query, task_id)
        sql_times.append(time.perf_counter() - t0)
        last_resp = resp
    res = last_resp.get("result", {})
    sc = res.get("structuredContent", {})
    r = sc.get("results", [{}])
    if r:
        rows = len(r[0].get("rows", []))
    c.close()
    return {
        "sql_min": round(min(sql_times), 3),
        "sql_median": round(median(sql_times), 3),
        "sql_max": round(max(sql_times), 3),
        "rows": rows,
    }

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--gh-cmd", required=True)
    ap.add_argument("--query", required=True)
    ap.add_argument("--task-id", required=True)
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--test", required=True)
    args = ap.parse_args()
    os.makedirs(os.path.join(args.outdir, args.test), exist_ok=True)
    gh = run_gh(args.gh_cmd, args.runs)
    coral = run_coral_warm(args.query, args.task_id, args.runs,
                           os.path.join(args.outdir, args.test, "warm_mcp.log"))
    print("WARM CORAL (server started once, %d queries against the same session):" % args.runs)
    print("  gh   :", gh)
    print("  coral:", coral)
    summary = {"gh": gh, "coral_warm": coral, "runs": args.runs}
    with open(os.path.join(args.outdir, args.test, "warm_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    ratio = round(coral["sql_median"] / gh["real_median"], 2) if gh["real_median"] else None
    print("  ratio (coral sql / gh):", ratio)
