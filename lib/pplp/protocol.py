from pplp.graph import Graph
from pplp.psi import psi_cardinality


class DirectLinkFound(Exception):
    """Raised when x and y are direct neighbors in graph2.

    Per the paper (Section 2.2, assumption 4), Graph 2 halts and informs
    Graph 1 that a direct link exists, which is stronger evidence than CN.
    """


def _validate_pair(graph1: Graph, graph2_or_client, x: str, y: str, *, remote: bool = False):
    if graph1.has_edge(x, y):
        raise ValueError(
            f"{x} and {y} are direct neighbors in graph1; "
            "no need for the computation"
        )
    if not remote and graph2_or_client.has_edge(x, y):
        raise DirectLinkFound(f"{x} and {y} are direct neighbors in graph2")


def compute_cn(graph1: Graph, graph2: Graph, x: str, y: str) -> int:
    _validate_pair(graph1, graph2, x, y)

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


def compute_jaccard(graph1: Graph, graph2: Graph, x: str, y: str) -> float:
    _validate_pair(graph1, graph2, x, y)

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

    cn = local1 + local2 + crossover1 + crossover2 - overlap

    deg_overlap_x = psi_cardinality(graph1.neighbors(x), graph2.neighbors(x))
    deg_overlap_y = psi_cardinality(graph1.neighbors(y), graph2.neighbors(y))
    degree_x = len(graph1.neighbors(x)) + len(graph2.neighbors(x)) - deg_overlap_x
    degree_y = len(graph1.neighbors(y)) + len(graph2.neighbors(y)) - deg_overlap_y
    union = degree_x + degree_y - cn

    return cn / union if union > 0 else 0.0


def compute_cn_remote(graph1: Graph, party2_client, x: str, y: str) -> int:
    """Distributed compute_cn — Party 1 holds graph1, Party 2 is a remote HTTP service.

    Args:
        graph1:        Party 1's graph.
        party2_client: An httpx.Client or FastAPI TestClient pointed at Party 2's server.
        x, y:          The candidate node pair (must match node IDs used in both graphs).
    """
    from pplp.psi_client import remote_psi_cardinality

    _validate_pair(graph1, party2_client, x, y, remote=True)

    prep_resp = party2_client.post("/prepare", json={"x": x, "y": y})
    prep_resp.raise_for_status()
    prep = prep_resp.json()

    local2 = prep["local2"]
    session_id = prep["session_id"]

    local1_set = graph1.local_intersection(x, y)
    local1 = len(local1_set)

    g1_x = graph1.neighbors(x) - local1_set
    g1_y = graph1.neighbors(y) - local1_set

    crossover1 = remote_psi_cardinality(party2_client, g1_x, session_id, "crossover1")
    crossover2 = remote_psi_cardinality(party2_client, g1_y, session_id, "crossover2")
    overlap = remote_psi_cardinality(party2_client, local1_set, session_id, "overlap")

    return local1 + local2 + crossover1 + crossover2 - overlap


def compute_jaccard_remote(graph1: Graph, party2_client, x: str, y: str) -> float:
    """Distributed Jaccard — requires 5 PSI calls (3 for CN + 2 for degree overlap).

    Party 2 also reveals |Γ₂(x)| and |Γ₂(y)| (degree info) in the prepare response.
    """
    from pplp.psi_client import remote_psi_cardinality

    _validate_pair(graph1, party2_client, x, y, remote=True)

    prep_resp = party2_client.post(
        "/prepare", json={"x": x, "y": y, "measure": "jaccard"}
    )
    prep_resp.raise_for_status()
    prep = prep_resp.json()

    local2 = prep["local2"]
    session_id = prep["session_id"]
    degree2_x = prep["degree2_x"]
    degree2_y = prep["degree2_y"]

    local1_set = graph1.local_intersection(x, y)
    local1 = len(local1_set)

    g1_x = graph1.neighbors(x) - local1_set
    g1_y = graph1.neighbors(y) - local1_set

    crossover1 = remote_psi_cardinality(party2_client, g1_x, session_id, "crossover1")
    crossover2 = remote_psi_cardinality(party2_client, g1_y, session_id, "crossover2")
    overlap = remote_psi_cardinality(party2_client, local1_set, session_id, "overlap")

    cn = local1 + local2 + crossover1 + crossover2 - overlap

    deg_overlap_x = remote_psi_cardinality(
        party2_client, graph1.neighbors(x), session_id, "degree_x"
    )
    deg_overlap_y = remote_psi_cardinality(
        party2_client, graph1.neighbors(y), session_id, "degree_y"
    )
    degree_x = len(graph1.neighbors(x)) + degree2_x - deg_overlap_x
    degree_y = len(graph1.neighbors(y)) + degree2_y - deg_overlap_y
    union = degree_x + degree_y - cn

    return cn / union if union > 0 else 0.0
