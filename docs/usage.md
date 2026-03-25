# Usage Guide

## Installation

```bash
pip install pplp
```

## Setup

Each party installs `pplp` independently on their own machine. Node IDs must match across both graphs (e.g., both use email addresses or phone numbers for shared nodes).

## Party 2: start the server

Party 2 prepares a CSV edge list (no header, one edge per line) and starts the server:

```
Alice,Bob
Alice,Charlie
Bob,Dave
```

```bash
pplp-server party2_graph.csv --host 0.0.0.0 --port 8000
```

Options:

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | `0.0.0.0` | Bind address |
| `--port` | `8000` | Port |

## Party 1: run the query

Party 1 builds their graph in Python and connects to Party 2's server:

```python
from pplp import Graph, compute_cn_remote, party2_client

graph1 = Graph.from_edge_list([
    ("Alice", "Bob"), ("Alice", "Charlie"), ("Alice", "Grace"), ("Alice", "Henry"),
    ("Eve", "Charlie"), ("Eve", "Diana"),
])

with party2_client("http://<party2-ip>:8000") as client:
    cn = compute_cn_remote(graph1, client, "Alice", "Eve")
    print(f"Common Neighbors: {cn}")
```

Only Party 1 learns the result. Party 2's graph structure is never revealed.

## Building graphs

```python
from pplp import Graph

# From an edge list
graph = Graph.from_edge_list([
    ("alice", "bob"),
    ("alice", "charlie"),
    ("bob", "dave"),
])

# Or incrementally
graph = Graph()
graph.add_edge("alice", "bob")
graph.add_edge("alice", "charlie")
```

## Handling edge cases

### Direct neighbors

If the candidate pair is already directly connected, there's no need for link prediction:

```python
try:
    cn = compute_cn_remote(graph1, client, "Alice", "Eve")
except ValueError:
    # Alice and Eve are already direct neighbors in Party 1's graph
    print("Already connected in your graph")
except DirectLinkFound:
    # Alice and Eve are direct neighbors in Party 2's graph
    print("Direct link exists in the other party's graph")
```

### Missing nodes

If a node doesn't exist in one graph, its neighbor set is treated as empty — the protocol still works, you just get zero contribution from that side.

## What's happening under the hood

For a candidate pair (x, y), `compute_cn_remote` runs the Demirag/Ayday et al. protocol over HTTP:

1. Party 1 calls `/prepare` — Party 2 checks for a direct link and returns its local intersection size
2. Three **PSI-cardinality** calls (each a pair of HTTP round-trips to `/psi/{id}/setup` and `/psi/{id}/respond`) reveal only the *sizes* of crossover intersections
3. Party 1 combines: `CN = local1 + local2 + crossover1 + crossover2 - overlap`

No raw neighbor sets are ever exchanged. See [Protocol Details](protocol.md) for the full breakdown.
