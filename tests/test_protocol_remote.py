import pytest
from fastapi.testclient import TestClient

from pplp.graph import Graph
from pplp.protocol import compute_cn_remote, DirectLinkFound
from pplp.server.app import create_app


def _graphs():
    g1 = Graph.from_edge_list([
        ("A", "B"), ("A", "C"), ("A", "G"), ("A", "H"),
        ("E", "C"), ("E", "D"),
    ])
    g2 = Graph.from_edge_list([
        ("A", "C"), ("A", "F"), ("A", "K"),
        ("E", "B"), ("E", "C"), ("E", "D"), ("E", "F"),
    ])
    return g1, g2


def test_paper_example_remote():
    g1, g2 = _graphs()
    party2 = TestClient(create_app(g2))
    assert compute_cn_remote(g1, party2, "A", "E") == 3


def test_remote_matches_local():
    from pplp.protocol import compute_cn
    g1, g2 = _graphs()
    party2 = TestClient(create_app(g2))
    assert compute_cn_remote(g1, party2, "A", "E") == compute_cn(g1, g2, "A", "E")


def test_remote_direct_link_graph1_raises():
    g1 = Graph.from_edge_list([("A", "B")])
    g2 = Graph.from_edge_list([("A", "C"), ("B", "C")])
    party2 = TestClient(create_app(g2))
    with pytest.raises(ValueError, match="direct neighbors in graph1"):
        compute_cn_remote(g1, party2, "A", "B")


def test_remote_direct_link_graph2_runs_protocol():
    # Security: if x-y is a direct edge in graph2 only, the server must run PPLP
    # as normal without signaling the edge. CN here is the count of shared
    # neighbors between A and B across both graphs ({C} → 1).
    g1 = Graph.from_edge_list([("A", "C"), ("B", "C")])
    g2 = Graph.from_edge_list([("A", "B")])
    party2 = TestClient(create_app(g2))
    assert compute_cn_remote(g1, party2, "A", "B") == 1


def test_remote_no_common_neighbors():
    # Non-empty but fully disjoint neighbor sets — PSI calls actually fire
    g1 = Graph.from_edge_list([("X", "P"), ("Y", "Q")])
    g2 = Graph.from_edge_list([("X", "R"), ("Y", "S")])
    party2 = TestClient(create_app(g2))
    assert compute_cn_remote(g1, party2, "X", "Y") == 0
