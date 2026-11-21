"""runpod.py and create_one.py on the Runpod v2 API (rest.runpod.io retired 2026-11-21). The output contract the frozen
launcher and podctl.py read is unchanged; every test fakes the HTTP layer, so no request reaches Runpod."""
import json, subprocess, sys
import pytest
import runpod as RP

POD = {"id": "p1", "name": "ts-rep", "status": "RUNNING", "cost": 0.48, "cpu": {"id": "cpu3c", "vcpuCount": 16, "memory": 32},
       "ssh": {"proxy": None, "direct": {"host": "1.2.3.4", "port": 40022, "username": "root", "command": "ssh"}}}


def fake_http(pages):
    calls = []
    def h(method, path, body=None):
        calls.append((method, path, body))
        return pages[len(calls) - 1]
    h.calls = calls
    return h


def test_base_is_v2():
    assert RP.BASE == "https://api.runpod.io/v2"


def test_list_maps_v2_to_the_old_fields(monkeypatch, capsys):
    monkeypatch.setattr(RP, "_http", fake_http([(200, {"pods": [POD], "pagination": {"hasNextPage": False, "nextCursor": None}})]))
    assert RP.main(["list"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out == [{"id": "p1", "name": "ts-rep", "desiredStatus": "RUNNING", "publicIp": "1.2.3.4",
                    "portMappings": {"22": 40022}, "costPerHr": 0.48, "vcpuCount": 16}]


def test_list_follows_the_cursor(monkeypatch, capsys):
    p2 = dict(POD, id="p2")
    h = fake_http([(200, {"pods": [POD], "pagination": {"hasNextPage": True, "nextCursor": "c1"}}),
                   (200, {"pods": [p2], "pagination": {"hasNextPage": False, "nextCursor": None}})])
    monkeypatch.setattr(RP, "_http", h)
    assert RP.main(["list"]) == 0
    assert [p["id"] for p in json.loads(capsys.readouterr().out)] == ["p1", "p2"]
    assert h.calls[1][1].endswith("cursor=c1")


def test_list_drops_terminated_pods(monkeypatch, capsys):
    monkeypatch.setattr(RP, "_http", fake_http([(200, {"pods": [POD, dict(POD, id="gone", status="TERMINATED")],
                                                       "pagination": {"hasNextPage": False, "nextCursor": None}})]))
    assert RP.main(["list"]) == 0
    assert [p["id"] for p in json.loads(capsys.readouterr().out)] == ["p1"]


def test_list_without_direct_ssh_has_no_address(monkeypatch, capsys):
    monkeypatch.setattr(RP, "_http", fake_http([(200, {"pods": [dict(POD, ssh={"proxy": None, "direct": None})],
                                                       "pagination": {"hasNextPage": False, "nextCursor": None}})]))
    assert RP.main(["list"]) == 0
    p = json.loads(capsys.readouterr().out)[0]
    assert p["publicIp"] is None and p["portMappings"] == {}


@pytest.mark.parametrize("answer", [
    (200, []), (200, {"pods": "x", "pagination": {}}), (200, {"pagination": {"hasNextPage": False}}),
    (200, {"pods": [], "pagination": "x"}), (200, {"pods": [], "pagination": {"hasNextPage": True, "nextCursor": None}}),
    (200, {"pods": ["x"], "pagination": {"hasNextPage": False, "nextCursor": None}}),
    (200, {"pods": [{"name": "n"}], "pagination": {"hasNextPage": False, "nextCursor": None}}),
    (401, {"error": 401, "body": ""}), (500, {"error": 500, "body": ""}), (200, None)])
def test_list_fails_closed_on_any_unexpected_answer(monkeypatch, capsys, answer):
    """A wrong shape must never print [] (no pod) while a pod may bill: podctl reads a non-zero exit as a failed listing."""
    monkeypatch.setattr(RP, "_http", fake_http([answer]))
    assert RP.main(["list"]) != 0
    assert capsys.readouterr().out == ""


def test_list_fails_closed_on_a_network_error(monkeypatch, capsys):
    def boom(*a, **k): raise OSError("no route")
    monkeypatch.setattr(RP, "_http", boom)
    assert RP.main(["list"]) != 0
    assert capsys.readouterr().out == ""


def test_target_reads_the_direct_ssh_endpoint(monkeypatch):
    monkeypatch.setattr(RP, "_http", fake_http([(200, POD)]))
    assert RP.target("p1") == ("1.2.3.4", 40022)
    monkeypatch.setattr(RP, "_http", fake_http([(200, dict(POD, ssh={"proxy": None, "direct": None}))]))
    assert RP.target("p1") == (None, None)


def test_ssh_without_an_address_fails(monkeypatch):
    monkeypatch.setattr(RP, "_http", fake_http([(200, dict(POD, ssh={"proxy": None, "direct": None}))]))
    assert RP.main(["ssh", "p1", "echo up"]) != 0


def test_delete_accepts_204(monkeypatch, capsys):
    h = fake_http([(204, None)])
    monkeypatch.setattr(RP, "_http", h)
    assert RP.main(["delete", "p1"]) == 0
    assert h.calls == [("DELETE", "/pods/p1", None)]


def test_api_returns_the_old_error_dict(monkeypatch):
    monkeypatch.setattr(RP, "_http", fake_http([(400, {"error": 400, "body": "bad"})]))
    assert RP.api("POST", "/pods", {})["error"] == 400


# create_one.py: one request per call; 201 with an id is a pod; 202 (queued) and every unclear answer are ambiguous.
def run_create(monkeypatch, answer, index="0"):
    import importlib, io, contextlib
    h = fake_http([answer]) if not isinstance(answer, Exception) else None
    if h is None:
        def h(*a, **k): raise answer
        h.calls = []
    monkeypatch.setattr(RP, "_http", h)
    monkeypatch.setattr(sys, "argv", ["create_one.py", "ts-rep", index])
    sys.modules.pop("create_one", None)
    import os
    monkeypatch.syspath_prepend(os.path.dirname(os.path.abspath(__file__)))   # create_one.py inserts results/pods first
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), pytest.raises(SystemExit) as e:
        importlib.import_module("create_one")
    return e.value.code, json.loads(buf.getvalue().strip().splitlines()[-1]), h.calls


def test_create_sends_the_v2_cpu_body(monkeypatch):
    code, out, calls = run_create(monkeypatch, (201, dict(POD, id="new")))
    assert code == 0 and out["id"] == "new" and out["vcpu"] == 16
    method, path, body = calls[0]
    assert (method, path) == ("POST", "/pods")
    assert body["name"] == "ts-rep" and body["cpu"] == {"id": "cpu5c", "vcpuCount": 16} and body["cloud"] == "SECURE"
    assert body["ports"] == ["22/tcp"] and body["startSsh"] is True and body["disk"] == 20
    assert body["image"] == "runpod/base:0.6.2-cpu" and body["env"] == {"OMP_NUM_THREADS": "1"}
    assert "gpu" not in body and "queue" not in body


def test_create_202_queued_is_ambiguous(monkeypatch):
    code, out, _ = run_create(monkeypatch, (202, {"id": "q1", "status": "QUEUED", "podId": None}))
    assert code == 1 and out == {"id": "", "ambiguous": True}


@pytest.mark.parametrize("answer,amb", [((400, {"error": 400, "body": ""}), False), ((404, {"error": 404, "body": ""}), False),
                                         ((429, {"error": 429, "body": ""}), True), ((500, {"error": 500, "body": ""}), True),
                                         ((201, None), True), ((201, {"name": "x"}), True), ((200, dict(POD, id="x")), True)])
def test_create_classifies_other_answers(monkeypatch, answer, amb):
    code, out, _ = run_create(monkeypatch, answer)
    assert code == 1 and out == {"id": "", "ambiguous": amb}


def test_create_exception_is_ambiguous(monkeypatch):
    code, out, _ = run_create(monkeypatch, OSError("timeout"))
    assert code == 1 and out == {"id": "", "ambiguous": True}


# Review r1 (Sol 1-3, Astra 1-3).
END = {"hasNextPage": False, "nextCursor": None}


@pytest.mark.parametrize("pod", [{k: v for k, v in POD.items() if k != "name"}, dict(POD, name=None), dict(POD, name=7),
                                 dict(POD, id=7), dict(POD, id=""), dict(POD, name=None, status="TERMINATED")])
def test_list_rejects_a_pod_without_a_string_id_and_name(monkeypatch, capsys, pod):
    """A live pod whose name is missing would vanish from podctl.named(): reconcile and the watchdog would see no pod."""
    monkeypatch.setattr(RP, "_http", fake_http([(200, {"pods": [POD, pod], "pagination": END})]))
    assert RP.main(["list"]) != 0
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("pg", [{"hasNextPage": False, "nextCursor": "more"}, {"hasNextPage": False}, {"nextCursor": None},
                                {"hasNextPage": None, "nextCursor": None}, {"hasNextPage": True, "nextCursor": ""},
                                {"hasNextPage": True, "nextCursor": 5}, {"hasNextPage": "false", "nextCursor": None}])
def test_list_rejects_inconsistent_pagination(monkeypatch, capsys, pg):
    monkeypatch.setattr(RP, "_http", fake_http([(200, {"pods": [], "pagination": pg})]))
    assert RP.main(["list"]) != 0
    assert capsys.readouterr().out == ""


def test_list_rejects_a_bad_later_page(monkeypatch, capsys):
    monkeypatch.setattr(RP, "_http", fake_http([(200, {"pods": [POD], "pagination": {"hasNextPage": True, "nextCursor": "c"}}),
                                                (200, {"pods": [], "pagination": {"hasNextPage": False, "nextCursor": "x"}})]))
    assert RP.main(["list"]) != 0
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("answer,amb", [
    ((202, {"id": "queue-id", "error": 400}), True), ((200, {"error": 400}), True), ((201, {"error": 400}), True),
    ((201, {"id": 7}), True), ((201, {"id": ""}), True), ((201, dict(POD, id=None)), True),
    ((403, {"error": 403, "body": ""}), False), ((408, {"error": 408, "body": ""}), True), ((503, None), True),
    ((404, None), False), ((301, None), True)])
def test_create_classifies_by_http_status(monkeypatch, answer, amb):
    code, out, _ = run_create(monkeypatch, answer)
    assert code == 1 and out == {"id": "", "ambiguous": amb}


# Review r2: Sol 1 (cluster member pods are hidden unless includeClusterPods=true), Astra 1 (urlopen followed redirects).
def test_list_includes_cluster_pods_on_every_page(monkeypatch, capsys):
    h = fake_http([(200, {"pods": [POD], "pagination": {"hasNextPage": True, "nextCursor": "c/1"}}),
                   (200, {"pods": [], "pagination": END})])
    monkeypatch.setattr(RP, "_http", h)
    assert RP.main(["list"]) == 0
    assert h.calls[0][1] == "/pods?includeClusterPods=true"
    assert h.calls[1][1] == "/pods?includeClusterPods=true&cursor=c%2F1"


import http.server, threading


class _Srv:
    """A local HTTP server: POST/GET /v2/pods answers STATUS with a Location to /v2/next, which answers 404."""
    def __init__(self, status):
        hits = self.hits = []
        class H(http.server.BaseHTTPRequestHandler):
            def _go(self):
                hits.append((self.command, self.path))
                n = int(self.headers.get("Content-Length") or 0); self.rfile.read(n)
                if self.path.startswith("/v2/pods"):
                    self.send_response(status); self.send_header("Location", "/v2/next"); self.send_header("Content-Length", "0"); self.end_headers()
                else:
                    self.send_response(404); self.send_header("Content-Length", "0"); self.end_headers()
            do_GET = do_POST = _go
            def log_message(self, *a): pass
        self.s = http.server.HTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.s.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.s.server_address[1]}/v2"
    def close(self): self.s.shutdown(); self.s.server_close()


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
def test_transport_never_follows_a_redirect(monkeypatch, status):
    srv = _Srv(status)
    try:
        monkeypatch.setattr(RP, "BASE", srv.base)
        code, body = RP._http("POST", "/pods", {"name": "x"})
        assert code == status and srv.hits == [("POST", "/v2/pods")]
    finally:
        srv.close()


@pytest.mark.parametrize("status", [301, 302, 303])
def test_create_after_a_redirect_is_ambiguous_with_one_request(monkeypatch, status):
    srv = _Srv(status)
    try:
        monkeypatch.setattr(RP, "BASE", srv.base)
        import importlib, io, contextlib, os
        monkeypatch.setattr(sys, "argv", ["create_one.py", "ts-rep", "0"])
        monkeypatch.syspath_prepend(os.path.dirname(os.path.abspath(__file__)))
        sys.modules.pop("create_one", None)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), pytest.raises(SystemExit) as e:
            importlib.import_module("create_one")
        assert e.value.code == 1 and json.loads(buf.getvalue().strip().splitlines()[-1]) == {"id": "", "ambiguous": True}
        assert srv.hits == [("POST", "/v2/pods")]
    finally:
        srv.close()


@pytest.mark.parametrize("status", [301, 302, 303])
def test_list_after_a_redirect_fails_with_no_stdout(monkeypatch, capsys, status):
    srv = _Srv(status)
    try:
        monkeypatch.setattr(RP, "BASE", srv.base)
        assert RP.main(["list"]) != 0
        assert capsys.readouterr().out == "" and len(srv.hits) == 1
    finally:
        srv.close()
