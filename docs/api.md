# API Reference

## `Graph`

```python
from pplp import Graph
```

A simple undirected graph backed by an adjacency list. Node IDs are strings.

### `Graph()`

Create an empty graph.

### `Graph.from_edge_list(edges)`

Create a graph from a list of `(node_a, node_b)` tuples.

```python
g = Graph.from_edge_list([("A", "B"), ("B", "C")])
```

**Parameters:**

- `edges` — `list[tuple[str, str]]`

**Returns:** `Graph`

### `graph.add_edge(u, v)`

Add an undirected edge between nodes `u` and `v`. Creates nodes if they don't exist. Duplicate edges are silently ignored.

**Parameters:**

- `u` — `str`
- `v` — `str`

### `graph.neighbors(node)`

Return the neighbor set of a node. Returns an empty set if the node doesn't exist.

**Parameters:**

- `node` — `str`

**Returns:** `set[str]`

### `graph.has_edge(u, v)`

Check whether an edge exists between `u` and `v`.

**Returns:** `bool`

### `graph.local_intersection(x, y)`

Return the set of common neighbors of `x` and `y` within this graph: `neighbors(x) & neighbors(y)`.

**Returns:** `set[str]`

---

## `compute_cn`

```python
from pplp import compute_cn
```

### `compute_cn(graph1, graph2, x, y)`

Compute the Common Neighbors count for the candidate pair `(x, y)` across the joint graph of both parties, using the Demirag/Ayday et al. privacy-preserving protocol.

`graph1` is the **client** (learns the result). `graph2` is the **server** (learns nothing beyond what PSI leaks).

**Parameters:**

- `graph1` — `Graph` — the requesting party's graph
- `graph2` — `Graph` — the helper party's graph
- `x` — `str` — first node in the candidate pair
- `y` — `str` — second node in the candidate pair

**Returns:** `int` — the Common Neighbors count on the joint graph

**Raises:**

- `ValueError` — if `x` and `y` are direct neighbors in `graph1` (no need for the computation)
- `DirectLinkFound` — if `x` and `y` are direct neighbors in `graph2` (direct link is stronger evidence than CN)

---

## `compute_cn_remote`

```python
from pplp import compute_cn_remote
```

### `compute_cn_remote(graph1, party2_client, x, y)`

Distributed version of `compute_cn`. Party 1 holds `graph1` locally; Party 2 runs a remote HTTP server. The same Ayday et al. protocol is used — three PSI-cardinality calls — but each call is a pair of HTTP round-trips to Party 2's server.

**Parameters:**

- `graph1` — `Graph` — Party 1's private graph
- `party2_client` — `httpx.Client` (or compatible) — HTTP client pointed at Party 2's server, e.g. from `party2_client()`
- `x` — `str` — first node in the candidate pair
- `y` — `str` — second node in the candidate pair

**Returns:** `int` — the Common Neighbors count on the joint graph

**Raises:**

- `ValueError` — if `x` and `y` are direct neighbors in `graph1`
- `DirectLinkFound` — if `x` and `y` are direct neighbors in `graph2` (reported by Party 2 via `/prepare`)

---

## `party2_client`

```python
from pplp import party2_client
```

### `party2_client(base_url, timeout=30.0)`

Context manager that yields an `httpx.Client` configured to talk to Party 2's server. Use this with `compute_cn_remote`.

**Parameters:**

- `base_url` — `str` — base URL of Party 2's server, e.g. `"http://192.168.1.10:8000"`
- `timeout` — `float` — request timeout in seconds (default 30)

**Example:**

```python
with party2_client("http://192.168.1.10:8000") as client:
    cn = compute_cn_remote(graph1, client, "A", "E")
```

---

## `DirectLinkFound`

```python
from pplp import DirectLinkFound
```

Exception raised when the candidate pair `(x, y)` are direct neighbors in `graph2`. Per the paper (Section 2.2), Graph 2 halts and informs Graph 1 that a direct link exists, which is stronger evidence for link prediction than a Common Neighbors score.

Inherits from `Exception`.
