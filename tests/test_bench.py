import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


def test_pilot_gate_loose_bound_in_ci():
    from bench import bench_episode_ms
    ms = bench_episode_ms(n_runs=5)
    print(f"median episode time: {ms:.1f} ms")
    assert ms < 400.0
