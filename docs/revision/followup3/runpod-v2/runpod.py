"""Minimal Runpod REST helper on the v2 API (api.runpod.io/v2; rest.runpod.io/v1 was retired, 2026-11-21). Usage:
  python runpod.py list | balance | get ID | delete ID | ssh ID 'cmd' | push ID LOCAL REMOTE | pull ID REMOTE LOCAL
The output the launchers and podctl.py read is the v1 shape: `list` prints id, name, desiredStatus, publicIp,
portMappings, costPerHr and vcpuCount per pod, and exits non-zero (printing nothing) on any answer it cannot read, so a
failed listing is never mistaken for "no pod"."""
import json, os, re, subprocess, sys, urllib.parse, urllib.request
KEY = re.search(r"apikey\s*=\s*'([^']+)'", open(os.path.expanduser("~/.runpod/config.toml")).read()).group(1)
SSHKEY = os.path.expanduser("~/.runpod/ssh/runpodctl-ssh-key")
BASE = "https://api.runpod.io/v2"
HEADERS = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json", "User-Agent": "curl/8.7.1"}


def _http(method, path, body=None):
    """(HTTP status, parsed body); an HTTP error is (code, {"error": code, "body": text}); network errors raise."""
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode() if body else None, method=method, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            t = r.read().decode(); return r.status, (json.loads(t) if t else None)
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.code, "body": e.read().decode()[:500]}


def api(method, path, body=None):
    return _http(method, path, body)[1]


def _direct(p):
    d = (p.get("ssh") or {}).get("direct") if isinstance(p.get("ssh"), dict) else None
    return (d.get("host"), d.get("port")) if isinstance(d, dict) else (None, None)


def _v1(p):
    host, port = _direct(p)
    cpu = p.get("cpu") if isinstance(p.get("cpu"), dict) else {}
    return {"id": p["id"], "name": p.get("name"), "desiredStatus": p.get("status"), "publicIp": host,
            "portMappings": {"22": port} if port is not None else {}, "costPerHr": p.get("cost"), "vcpuCount": cpu.get("vcpuCount")}


def list_pods():
    """Every non-terminated pod in the v1 shape, following the cursor; ValueError on any answer it cannot read."""
    out, cursor = [], None
    for _ in range(1000):
        status, d = _http("GET", "/pods" + (f"?cursor={urllib.parse.quote(cursor)}" if cursor else ""))
        if status != 200 or not isinstance(d, dict) or not isinstance(d.get("pods"), list) or not isinstance(d.get("pagination"), dict):
            raise ValueError(f"unreadable pod listing (HTTP {status})")
        for p in d["pods"]:
            if not isinstance(p, dict) or not isinstance(p.get("id"), str) or not p["id"] or not isinstance(p.get("name"), str):
                raise ValueError("a pod without a string id and name")   # it would vanish from podctl.named()
            if p.get("status") != "TERMINATED":
                out.append(_v1(p))
        pg = d["pagination"]
        if "nextCursor" in pg and pg.get("hasNextPage") is False and pg["nextCursor"] is None:
            return out
        if pg.get("hasNextPage") is not True or not isinstance(pg.get("nextCursor"), str) or not pg["nextCursor"]:
            raise ValueError("unreadable or inconsistent pagination")
        cursor = pg["nextCursor"]
    raise ValueError("too many pages")


def target(pod_id):
    status, p = _http("GET", f"/pods/{pod_id}")
    return _direct(p) if status == 200 and isinstance(p, dict) else (None, None)


def ssh(pod_id, cmd, timeout=None):
    ip, port = target(pod_id)
    if not ip or not port:
        return subprocess.CompletedProcess([], 255, "", "no direct ssh endpoint")
    return subprocess.run(["ssh", "-i", SSHKEY, "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "-o", "LogLevel=ERROR", "-o", "ConnectTimeout=20", "-p", str(port), f"root@{ip}", cmd],
                          capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)


def rsync(pod_id, src, dst, pull=False):
    ip, port = target(pod_id)
    if not ip or not port:
        return subprocess.CompletedProcess([], 255, "", "no direct ssh endpoint")
    e = f"ssh -i {SSHKEY} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -p {port}"
    a, b = (f"root@{ip}:{src}", dst) if pull else (src, f"root@{ip}:{dst}")
    return subprocess.run(["rsync", "-az", "-e", e, a, b], capture_output=True, text=True)


def main(argv) -> int:
    cmd, args = argv[0], argv[1:]
    if cmd == "list":
        try:
            pods = list_pods()
        except (ValueError, OSError) as e:
            print(f"list failed: {e}", file=sys.stderr); return 1
        print(json.dumps(pods, indent=1))
    elif cmd == "balance":   # read-only account balance (r16 spend record); any failure exits non-zero
        q = json.dumps({"query": "query { myself { clientBalance currentSpendPerHr } }"}).encode()
        req = urllib.request.Request("https://api.runpod.io/graphql", data=q, method="POST", headers=HEADERS)
        with urllib.request.urlopen(req, timeout=60) as r:
            m = json.loads(r.read().decode())["data"]["myself"]
        print(json.dumps({"balance": m["clientBalance"], "spendPerHr": m["currentSpendPerHr"]}))
    elif cmd == "get":
        status, p = _http("GET", f"/pods/{args[0]}")
        print(json.dumps(_v1(p) if status == 200 and isinstance(p, dict) and p.get("id") else p, indent=1)[:1500])
    elif cmd == "delete": print(api("DELETE", f"/pods/{args[0]}"))
    elif cmd == "ssh": r = ssh(args[0], args[1]); print(r.stdout, r.stderr, "exit", r.returncode); return r.returncode
    elif cmd == "push": r = rsync(args[0], args[1], args[2]); print(r.stdout[-300:], r.stderr[-300:], "exit", r.returncode); return r.returncode
    elif cmd == "pull": r = rsync(args[0], args[1], args[2], pull=True); print(r.stdout[-300:], r.stderr[-300:], "exit", r.returncode); return r.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
