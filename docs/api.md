# API Reference

## `compute_cn_remote`

```python
from pplp import compute_cn_remote
```

### `compute_cn_remote(graph1, party2_client, x, y)`

Compute the Common Neighbors count for the candidate pair `(x, y)` across both parties' graphs using the Ayday et al. privacy-preserving protocol over HTTP.

Party 1 holds `graph1` locally and connects to Party 2's server. Only Party 1 learns the result.

**Parameters:**

- `graph1` — `Graph` — Party 1's private graph
- `party2_client` — HTTP client pointed at Party 2's server (use `party2_client()`)
- `x` — `str` — first node in the candidate pair
- `y` — `str` — second node in the candidate pair

**Returns:** `int` — Common Neighbors count on the joint graph

**Raises:**

- `ValueError` — if `x` and `y` are direct neighbors in `graph1`
- `DirectLinkFound` — if `x` and `y` are direct neighbors in `graph2` (reported by Party 2)

---

## `party2_client`

```python
from pplp import party2_client
```

### `party2_client(base_url, timeout=30.0)`

Context manager yielding an HTTP client configured for Party 2's server.

**Parameters:**

- `base_url` — `str` — Party 2's server URL, e.g. `"http://192.168.1.10:8000"`
- `timeout` — `float` — request timeout in seconds (default `30.0`)

**Example:**

```python
with party2_client("http://192.168.1.10:8000") as client:
    cn = compute_cn_remote(graph1, client, "A", "E")
```

---

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

Add an undirected edge. Creates nodes if they don't exist. Duplicate edges are silently ignored.

### `graph.neighbors(node)`

Return the neighbor set of a node. Returns an empty set if the node doesn't exist.

**Returns:** `set[str]`

### `graph.has_edge(u, v)`

Check whether an edge exists between `u` and `v`.

**Returns:** `bool`

### `graph.local_intersection(x, y)`

Return the set of common neighbors of `x` and `y` within this graph.

**Returns:** `set[str]`

---

## `DirectLinkFound`

```python
from pplp import DirectLinkFound
```

Raised when the candidate pair `(x, y)` are direct neighbors in Party 2's graph. Per the paper (Section 2.2), this is stronger evidence for link prediction than a Common Neighbors score.

Inherits from `Exception`.

---

## `compute_cn` (local simulation)

```python
from pplp import compute_cn
```

### `compute_cn(graph1, graph2, x, y)`

Local version of the protocol — both graphs in the same process. Useful for testing and development; not for real two-party use.

**Parameters:** same as `compute_cn_remote` but takes a `Graph` instead of an HTTP client for `graph2`.

**Returns:** `int`

**Raises:** `ValueError`, `DirectLinkFound` (same conditions as `compute_cn_remote`)

---

## `pplp-server` CLI

```bash
pplp-server <graph_file> [--host HOST] [--port PORT]
```

Starts Party 2's FastAPI server. `graph_file` is a two-column CSV (no header) of edges:

```
Alice,Bob
Bob,Charlie
```

| Argument | Default | Description |
|----------|---------|-------------|
| `graph_file` | required | Path to edge-list CSV |
| `--host` | `0.0.0.0` | Bind address |
| `--port` | `8000` | Port |
| `--tunnel` | off | Expose via ngrok tunnel |
| `--tunnel-timeout` | `60` | Tunnel connection timeout (seconds) |

---

## Streamlit UI

```bash
uv run streamlit run app.py
```

A web interface for building graphs and running PPLP queries. See the [Usage Guide](usage.md#web-ui-streamlit-app) for details.

Requires `uv sync --extra ui` and `npm install -g localtunnel`.
