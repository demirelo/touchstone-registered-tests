"""runpod.py propagates the exit status of ssh, push and pull (internal review r7 of the reset plan)."""
import subprocess
import runpod as RP


def test_ssh_push_pull_return_the_subprocess_status(monkeypatch):
    fake = lambda *a, **k: subprocess.CompletedProcess([], 255, "", "boom")
    monkeypatch.setattr(RP, "ssh", fake); monkeypatch.setattr(RP, "rsync", fake)
    for argv in (["ssh", "p", "true"], ["push", "p", "a", "b"], ["pull", "p", "a", "b"]):
        assert RP.main(argv) == 255
    ok = lambda *a, **k: subprocess.CompletedProcess([], 0, "up", "")
    monkeypatch.setattr(RP, "ssh", ok)
    assert RP.main(["ssh", "p", "echo up"]) == 0
