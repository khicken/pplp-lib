# Usage Guide

## Installation

```bash
pip install pplp
```

Or with `uv`:

```bash
uv add pplp
```

## Building graphs

Each party constructs a `Graph` from their private data:

```python
from pplp import Graph

# From an edge list
graph = Graph.from_edge_list([
    ("alice", "bob"),
    ("alice", "charlie"),
    ("bob", "dave"),
])

# Or build incrementally
graph = Graph()
graph.add_edge("alice", "bob")
graph.add_edge("alice", "charlie")
```

Node IDs are strings. Both parties must agree on the same identifiers (e.g., email addresses, phone numbers) for shared nodes.

## Computing Common Neighbors

```python
from pplp import Graph, compute_cn, DirectLinkFound

# Party 1's graph
graph1 = Graph.from_edge_list([
    ("A", "B"), ("A", "C"), ("A", "G"), ("A", "H"),
    ("E", "C"), ("E", "D"),
])

# Party 2's graph
graph2 = Graph.from_edge_list([
    ("A", "C"), ("A", "F"), ("A", "K"),
    ("E", "B"), ("E", "C"), ("E", "D"), ("E", "F"),
])

# How many common neighbors do A and E have across both graphs?
cn = compute_cn(graph1, graph2, "A", "E")
print(cn)  # 3
```

`graph1` is the **client** (learns the result). `graph2` is the **server** (learns nothing). This asymmetry follows the paper's protocol.

## Handling edge cases

### Direct neighbors

If the candidate pair is already directly connected, there's no need for link prediction:

```python
try:
    cn = compute_cn(graph1, graph2, "A", "E")
except ValueError:
    # A and E are already direct neighbors in graph1
    print("Already connected in your graph")
except DirectLinkFound:
    # A and E are direct neighbors in graph2
    # This is stronger evidence than a CN score
    print("Direct link exists in the other party's graph")
```

### Missing nodes

If a node doesn't exist in one of the graphs, its neighbor set is treated as empty. The protocol still works — you just get zero contribution from that graph for that node.

```python
# Node "B" only exists in graph1
graph1 = Graph.from_edge_list([("A", "C"), ("B", "C")])
graph2 = Graph.from_edge_list([("A", "D")])

cn = compute_cn(graph1, graph2, "A", "B")  # returns 1 (only C)
```

## Querying the graph

```python
graph = Graph.from_edge_list([("A", "B"), ("A", "C"), ("B", "C")])

graph.neighbors("A")              # {"B", "C"}
graph.has_edge("A", "B")          # True
graph.local_intersection("A", "B")  # {"C"} — common neighbors within this graph
```

## What's happening under the hood

For a candidate pair (x, y), `compute_cn` runs the Demirag/Ayday et al. protocol:

1. Each party computes their **local** common neighbors of x and y
2. Three **PSI-cardinality** calls reveal only the *sizes* of crossover intersections
3. The result combines: `CN = local1 + local2 + crossover1 + crossover2 - overlap`

No raw neighbor sets are ever exchanged — only encrypted intersection sizes via the [OpenMined PSI](https://github.com/OpenMined/PSI) library (ECDH-based, cardinality-only mode).

!!! note "Current limitation"
    Both parties currently run in the same process. A network layer (so each party runs on a separate machine) is planned for a future release.
