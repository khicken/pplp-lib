import pytest
from fastapi.testclient import TestClient

from pplp.graph import Graph
from pplp.protocol import compute_jaccard, compute_jaccard_remote, DirectLinkFound
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


def test_paper_example_jaccard_remote():
    g1, g2 = _graphs()
    party2 = TestClient(create_app(g2))
    assert compute_jaccard_remote(g1, party2, "A", "E") == pytest.approx(3 / 7)


def test_remote_matches_local_jaccard():
    g1, g2 = _graphs()
    party2 = TestClient(create_app(g2))
    assert compute_jaccard_remote(g1, party2, "A", "E") == pytest.approx(
        compute_jaccard(g1, g2, "A", "E")
    )


def test_remote_direct_link_graph1_jaccard():
    g1 = Graph.from_edge_list([("A", "B")])
    g2 = Graph.from_edge_list([("A", "C"), ("B", "C")])
    party2 = TestClient(create_app(g2))
    with pytest.raises(ValueError, match="direct neighbors in graph1"):
        compute_jaccard_remote(g1, party2, "A", "B")


def test_remote_direct_link_graph2_runs_protocol():
    # Security: server must not halt/signal on a direct graph2 edge; run PPLP as normal.
    g1 = Graph.from_edge_list([("A", "C"), ("B", "C")])
    g2 = Graph.from_edge_list([("A", "B")])
    party2 = TestClient(create_app(g2))
    result = compute_jaccard_remote(g1, party2, "A", "B")
    assert 0.0 <= result <= 1.0


def test_remote_no_common_neighbors_jaccard():
    g1 = Graph.from_edge_list([("X", "P"), ("Y", "Q")])
    g2 = Graph.from_edge_list([("X", "R"), ("Y", "S")])
    party2 = TestClient(create_app(g2))
    assert compute_jaccard_remote(g1, party2, "X", "Y") == 0.0
