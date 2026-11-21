"""Minimal Runpod REST helper. Usage:
  python runpod.py list | balance | get ID | delete ID | ssh ID 'cmd' | push ID LOCAL REMOTE | pull ID REMOTE LOCAL"""
import json, os, re, subprocess, sys, urllib.request
KEY = re.search(r"apikey\s*=\s*'([^']+)'", open(os.path.expanduser("~/.runpod/config.toml")).read()).group(1)
SSHKEY = os.path.expanduser("~/.runpod/ssh/runpodctl-ssh-key")
BASE = "https://rest.runpod.io/v1"
def api(method, path, body=None):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode() if body else None, method=method,
                                 headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json", "User-Agent": "curl/8.7.1"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            t = r.read().decode(); return json.loads(t) if t else None
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read().decode()[:500]}
def target(pod_id):
    p = api("GET", f"/pods/{pod_id}"); pm = p.get("portMappings") or {}
    return p.get("publicIp"), pm.get("22") or pm.get(22)
def ssh(pod_id, cmd, timeout=None):
    ip, port = target(pod_id)
    return subprocess.run(["ssh", "-i", SSHKEY, "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "-o", "LogLevel=ERROR", "-o", "ConnectTimeout=20", "-p", str(port), f"root@{ip}", cmd],
                          capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
def rsync(pod_id, src, dst, pull=False):
    ip, port = target(pod_id)
    e = f"ssh -i {SSHKEY} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -p {port}"
    a, b = (f"root@{ip}:{src}", dst) if pull else (src, f"root@{ip}:{dst}")
    return subprocess.run(["rsync", "-az", "-e", e, a, b], capture_output=True, text=True)
def main(argv) -> int:
    cmd, args = argv[0], argv[1:]
    if cmd == "list": print(json.dumps([{k: p.get(k) for k in ("id", "name", "desiredStatus", "publicIp", "portMappings", "costPerHr", "vcpuCount")} for p in api("GET", "/pods")], indent=1))
    elif cmd == "balance":   # read-only account balance (r16 spend record); any failure exits non-zero
        q = json.dumps({"query": "query { myself { clientBalance currentSpendPerHr } }"}).encode()
        req = urllib.request.Request("https://api.runpod.io/graphql", data=q, method="POST",
                                     headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json", "User-Agent": "curl/8.7.1"})
        with urllib.request.urlopen(req, timeout=60) as r:
            m = json.loads(r.read().decode())["data"]["myself"]
        print(json.dumps({"balance": m["clientBalance"], "spendPerHr": m["currentSpendPerHr"]}))
    elif cmd == "get": print(json.dumps(api("GET", f"/pods/{args[0]}"), indent=1)[:1500])
    elif cmd == "delete": print(api("DELETE", f"/pods/{args[0]}"))
    elif cmd == "ssh": r = ssh(args[0], args[1]); print(r.stdout, r.stderr, "exit", r.returncode); return r.returncode
    elif cmd == "push": r = rsync(args[0], args[1], args[2]); print(r.stdout[-300:], r.stderr[-300:], "exit", r.returncode); return r.returncode
    elif cmd == "pull": r = rsync(args[0], args[1], args[2], pull=True); print(r.stdout[-300:], r.stderr[-300:], "exit", r.returncode); return r.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
