import pytest
from fastapi.testclient import TestClient

from pplp.graph import Graph
from pplp.psi_client import remote_psi_cardinality
from pplp.server.app import create_app


def _g2():
    return Graph.from_edge_list([("A", "C"), ("A", "F"), ("A", "K"),
                                  ("E", "B"), ("E", "C"), ("E", "D"), ("E", "F")])


def _session(client, x="A", y="E"):
    return client.post("/prepare", json={"x": x, "y": y}).json()["session_id"]


def test_remote_psi_cardinality_correct_count():
    # crossover1: Party 2 has g2_y = {B, D}; Party 1 sends {H, G, B} → intersection = {B} = 1
    app = create_app(_g2())
    http_client = TestClient(app)
    sid = _session(http_client)
    assert remote_psi_cardinality(http_client, {"H", "G", "B"}, sid, "crossover1") == 1


def test_remote_psi_cardinality_no_intersection():
    # Z, W are not in any of g2's sets
    app = create_app(_g2())
    http_client = TestClient(app)
    sid = _session(http_client)
    assert remote_psi_cardinality(http_client, {"Z", "W"}, sid, "crossover1") == 0


def test_remote_psi_cardinality_empty_client_set_returns_zero_without_http():
    # Empty set short-circuits before making any HTTP call
    app = create_app(_g2())
    http_client = TestClient(app)
    sid = _session(http_client)
    assert remote_psi_cardinality(http_client, set(), sid, "crossover1") == 0
