from pplp.graph import Graph
from pplp.psi import psi_cardinality


class DirectLinkFound(Exception):
    """Raised when x and y are direct neighbors in graph2.

    Per the paper (Section 2.2, assumption 4), Graph 2 halts and informs
    Graph 1 that a direct link exists, which is stronger evidence than CN.
    """


def compute_cn(graph1: Graph, graph2: Graph, x: str, y: str) -> int:
    if graph1.has_edge(x, y):
        raise ValueError(
            f"{x} and {y} are direct neighbors in graph1; "
            "no need for the computation"
        )
    if graph2.has_edge(x, y):
        raise DirectLinkFound(
            f"{x} and {y} are direct neighbors in graph2"
        )

    local1_set = graph1.local_intersection(x, y)
    local2_set = graph2.local_intersection(x, y)
    local1 = len(local1_set)
    local2 = len(local2_set)

    g1_x = graph1.neighbors(x) - local1_set
    g1_y = graph1.neighbors(y) - local1_set
    g2_x = graph2.neighbors(x) - local2_set
    g2_y = graph2.neighbors(y) - local2_set

    crossover1 = psi_cardinality(g1_x, g2_y)
    crossover2 = psi_cardinality(g1_y, g2_x)
    overlap = psi_cardinality(local1_set, local2_set)

    return local1 + local2 + crossover1 + crossover2 - overlap
