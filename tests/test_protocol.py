import pytest
from pplp.graph import Graph
from pplp.protocol import compute_cn, DirectLinkFound


def _make_paper_graphs():
    """Graphs from the presentation example (nodes A and E, CN=3)."""
    g1 = Graph.from_edge_list([
        ("A", "B"), ("A", "C"), ("A", "G"), ("A", "H"),
        ("E", "C"), ("E", "D"),
    ])
    g2 = Graph.from_edge_list([
        ("A", "C"), ("A", "F"), ("A", "K"),
        ("E", "B"), ("E", "C"), ("E", "D"), ("E", "F"),
    ])
    return g1, g2


def test_paper_example():
    g1, g2 = _make_paper_graphs()
    assert compute_cn(g1, g2, "A", "E") == 3


def test_matches_naive_cn():
    """compute_cn should match a plain set intersection on the merged graph."""
    g1, g2 = _make_paper_graphs()

    merged_neighbors_a = g1.neighbors("A") | g2.neighbors("A")
    merged_neighbors_e = g1.neighbors("E") | g2.neighbors("E")
    naive_cn = len(merged_neighbors_a & merged_neighbors_e)

    assert compute_cn(g1, g2, "A", "E") == naive_cn


def test_no_common_neighbors():
    g1 = Graph.from_edge_list([("X", "A")])
    g2 = Graph.from_edge_list([("Y", "B")])
    assert compute_cn(g1, g2, "X", "Y") == 0


def test_node_missing_from_one_graph():
    g1 = Graph.from_edge_list([("A", "C"), ("B", "C")])
    g2 = Graph.from_edge_list([("A", "D")])
    # B not in g2, so g2 contributes nothing for B's neighbors
    assert compute_cn(g1, g2, "A", "B") == 1  # C is the only CN


def test_both_nodes_missing_from_graph2():
    g1 = Graph.from_edge_list([("A", "C"), ("B", "C")])
    g2 = Graph.from_edge_list([("X", "Y")])
    assert compute_cn(g1, g2, "A", "B") == 1


def test_direct_neighbors_graph1():
    g1 = Graph.from_edge_list([("A", "B")])
    g2 = Graph.from_edge_list([("A", "C"), ("B", "C")])
    with pytest.raises(ValueError, match="direct neighbors in graph1"):
        compute_cn(g1, g2, "A", "B")


def test_direct_neighbors_graph2():
    g1 = Graph.from_edge_list([("A", "C"), ("B", "C")])
    g2 = Graph.from_edge_list([("A", "B")])
    with pytest.raises(DirectLinkFound):
        compute_cn(g1, g2, "A", "B")
