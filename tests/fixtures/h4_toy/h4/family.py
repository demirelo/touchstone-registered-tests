"""A toy H4 bundle for tests only: D2+H3's knobs in a Family named H4."""
from dataclasses import replace

from sim.policies.families import FAMILIES
from sim.policies.identity import h3_family

BINARY = ("x", "clip")


def make_family(T, L):
    return replace(h3_family(FAMILIES["D2"]), name="H4")
