import argparse, json, os, resource, select, statistics, subprocess, sys, time

def median(vals):
    return statistics.median(vals) if vals else float("nan")

def run_gh(cmd):
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    t0 = time.perf_counter()
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    wall = time.perf_counter() - t0
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    return {
        "real": wall,
        "user": after.ru_utime - before.ru_utime,
        "sys": after.ru_stime - before.ru_stime,
        "rc": p.returncode,
        "stdout": p.stdout,
        "stderr": p.stderr,
    }

def run_coral(query, task_id, intent, log_path):
    proc = subprocess.Popen(
        ["coral", "mcp-stdio"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=open(log_path, "w"), text=True, bufsize=1,
    )
    def send(o):
        proc.stdin.write(json.dumps(o) + "\n")
        proc.stdin.flush()
    def read_response(eid, timeout=300):
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
                     "clientInfo": {"name": "bench-runner", "version": "1.0"}}})
    read_response(1)
    t1 = time.time()
    send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
    send({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
          "params": {"name": "sql",
                     "arguments": {"queries": [query], "intent": intent, "task_id": task_id}}})
    resp = read_response(2)
    t2 = time.time()
    res = resp.get("result", {})
    sc = res.get("structuredContent", {})
    results = sc.get("results", []) if sc else []
    rows = results[0].get("rows", []) if results else []
    out = "init: %.2fs | sql: %.2fs | TOTAL: %.2fs\n" % (t1 - t0, t2 - t1, t2 - t0)
    out += "isError: %s | rows_returned: %d\n" % (res.get("isError"), len(rows))
    for r in rows[:3]:
        out += "ROW: %s\n" % json.dumps(r)[:180]
    proc.kill()
    return {
        "init": t1 - t0,
        "sql": t2 - t1,
        "total": t2 - t0,
        "isError": res.get("isError"),
        "rows": len(rows),
        "stdout": out,
    }

def main():
    ap = argparse.ArgumentParser(description="Repeatable gh-vs-coral timing benchmark runner")
    ap.add_argument("--tools", nargs="+", choices=["gh", "coral"], default=["gh", "coral"])
    ap.add_argument("--gh-cmd", help="shell command for the gh side")
    ap.add_argument("--query", help="SQL query for the coral side")
    ap.add_argument("--task-id", default="9fb7d5b2-ca35-4233-8ee1-5f9e45e659f5")
    ap.add_argument("--intent", default="benchmark")
    ap.add_argument("--test", required=True, help="test name; becomes the artifacts folder name")
    ap.add_argument("--runs", type=int, default=5, help="measured runs per tool")
    ap.add_argument("--warmup", type=int, default=3, help="warm-up runs per tool (discarded)")
    ap.add_argument("--outdir", help="parent dir for artifacts (default: ./artifacts)")
    args = ap.parse_args()

    if "gh" in args.tools and not args.gh_cmd:
        ap.error("--gh-cmd is required when running the gh tool")
    if "coral" in args.tools and not args.query:
        ap.error("--query is required when running the coral tool")

    root = args.outdir or "artifacts"
    base = os.path.join(root, args.test)
    os.makedirs(base, exist_ok=True)

    results = {}
    for tool in args.tools:
        tool_dir = os.path.join(base, tool)
        os.makedirs(tool_dir, exist_ok=True)
        runs = []
        total = args.warmup + args.runs
        for i in range(1, total + 1):
            run_dir = os.path.join(tool_dir, "run-%02d" % i)
            os.makedirs(run_dir, exist_ok=True)
            if tool == "gh":
                r = run_gh(args.gh_cmd)
                with open(os.path.join(run_dir, "out.txt"), "w") as f:
                    f.write(r["stdout"])
                with open(os.path.join(run_dir, "err.txt"), "w") as f:
                    f.write(r["stderr"])
                with open(os.path.join(run_dir, "timing.txt"), "w") as f:
                    f.write("real %.2f\nuser %.2f\nsys %.2f\n" % (r["real"], r["user"], r["sys"]))
                metric = {"real": r["real"]}
            else:
                log_path = os.path.join(run_dir, "mcp.log")
                r = run_coral(args.query, args.task_id, args.intent, log_path)
                with open(os.path.join(run_dir, "out.txt"), "w") as f:
                    f.write(r["stdout"])
                metric = {"init": r["init"], "sql": r["sql"], "total": r["total"], "rows": r["rows"]}
            sys.stderr.write("%s run %02d/%02d  %s\n" % (tool, i, total, json.dumps(metric)))
            if i > args.warmup:
                runs.append({"run": i - args.warmup, **metric})
        summary = {}
        keys = list(runs[0].keys()) if runs else []
        for k in keys:
            if k == "run":
                continue
            vals = [r[k] for r in runs if k in r]
            if vals and all(isinstance(v, (int, float)) for v in vals):
                summary[k] = {
                    "min": round(min(vals), 2),
                    "median": round(median(vals), 2),
                    "max": round(max(vals), 2),
                }
        summary["runs"] = len(runs)
        with open(os.path.join(tool_dir, "summary.json"), "w") as f:
            json.dump(summary, f, indent=2)
        results[tool] = summary
        sys.stderr.write("%s summary: %s\n" % (tool, json.dumps(summary)))

    print("\n## %s (median of %d runs, %d warm-up discarded)\n" % (args.test, args.runs, args.warmup))
    for tool in args.tools:
        s = results[tool]
        parts = " | ".join("%s: %s (min %s, max %s)" % (k, v["median"], v["min"], v["max"])
                           for k, v in s.items() if isinstance(v, dict))
        print("**%s:** %s\n" % (tool, parts))
    with open(os.path.join(base, "summary.json"), "w") as f:
        json.dump(results, f, indent=2)
    print("artifacts -> %s" % base)

if __name__ == "__main__":
    main()
