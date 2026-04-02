import pytest
from pplp.graph import Graph
from pplp.protocol import compute_jaccard, DirectLinkFound


def _make_paper_graphs():
    g1 = Graph.from_edge_list([
        ("A", "B"), ("A", "C"), ("A", "G"), ("A", "H"),
        ("E", "C"), ("E", "D"),
    ])
    g2 = Graph.from_edge_list([
        ("A", "C"), ("A", "F"), ("A", "K"),
        ("E", "B"), ("E", "C"), ("E", "D"), ("E", "F"),
    ])
    return g1, g2


def test_paper_example_jaccard():
    g1, g2 = _make_paper_graphs()
    result = compute_jaccard(g1, g2, "A", "E")
    # CN=3, merged neighbors: A={B,C,F,G,H,K}, E={B,C,D,F} → |A|=6, |E|=4, union=6+4-3=7
    assert result == pytest.approx(3 / 7)


def test_matches_naive_jaccard():
    g1, g2 = _make_paper_graphs()
    merged_a = g1.neighbors("A") | g2.neighbors("A")
    merged_e = g1.neighbors("E") | g2.neighbors("E")
    cn = len(merged_a & merged_e)
    union = len(merged_a | merged_e)
    naive = cn / union if union > 0 else 0.0
    assert compute_jaccard(g1, g2, "A", "E") == pytest.approx(naive)


def test_no_common_neighbors_jaccard():
    g1 = Graph.from_edge_list([("X", "A")])
    g2 = Graph.from_edge_list([("Y", "B")])
    assert compute_jaccard(g1, g2, "X", "Y") == 0.0


def test_identical_neighborhoods_jaccard():
    g1 = Graph.from_edge_list([("A", "C"), ("B", "C")])
    g2 = Graph.from_edge_list([("A", "C"), ("B", "C")])
    # CN=1 (C), |A|=1, |B|=1, union=2-1=1, jaccard=1.0
    assert compute_jaccard(g1, g2, "A", "B") == pytest.approx(1.0)


def test_direct_neighbors_graph1_jaccard():
    g1 = Graph.from_edge_list([("A", "B")])
    g2 = Graph.from_edge_list([("A", "C"), ("B", "C")])
    with pytest.raises(ValueError, match="direct neighbors in graph1"):
        compute_jaccard(g1, g2, "A", "B")


def test_direct_neighbors_graph2_jaccard():
    g1 = Graph.from_edge_list([("A", "C"), ("B", "C")])
    g2 = Graph.from_edge_list([("A", "B")])
    with pytest.raises(DirectLinkFound):
        compute_jaccard(g1, g2, "A", "B")
