from pplp.graph import Graph


def test_add_edge_and_neighbors():
    g = Graph()
    g.add_edge("A", "B")
    g.add_edge("A", "C")
    assert g.neighbors("A") == {"B", "C"}
    assert g.neighbors("B") == {"A"}


def test_neighbors_unknown_node():
    g = Graph()
    assert g.neighbors("X") == set()


def test_has_edge():
    g = Graph()
    g.add_edge("A", "B")
    assert g.has_edge("A", "B") is True
    assert g.has_edge("B", "A") is True
    assert g.has_edge("A", "C") is False


def test_local_intersection():
    g = Graph()
    g.add_edge("A", "C")
    g.add_edge("A", "D")
    g.add_edge("E", "C")
    g.add_edge("E", "F")
    assert g.local_intersection("A", "E") == {"C"}


def test_local_intersection_empty():
    g = Graph()
    g.add_edge("A", "B")
    g.add_edge("C", "D")
    assert g.local_intersection("A", "C") == set()


def test_from_edge_list():
    edges = [("A", "B"), ("B", "C")]
    g = Graph.from_edge_list(edges)
    assert g.neighbors("A") == {"B"}
    assert g.neighbors("B") == {"A", "C"}
