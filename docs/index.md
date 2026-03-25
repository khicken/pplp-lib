# PPLP

**Privacy-Preserving Link Prediction** — a Python library enabling two-party Common Neighbors link prediction over distributed graphs without revealing private graph structure.

Based on [Demirag/Ayday et al. 2022](https://arxiv.org/abs/2210.01297).

## What it does

Two parties (each holding a private graph on separate machines) can compute how many common neighbors a pair of nodes has across their **combined** graph — without either party revealing their edges to the other. This is useful for:

- **Social networks** — friend recommendations across platforms
- **E-commerce** — collaborative product recommendations
- **Telecommunications** — targeted advertising across carriers
- **Bioinformatics** — cross-institutional disease/gene association

## Quick start

**Party 2 — start the server:**

```bash
pip install pplp
pplp-server party2_graph.csv --host 0.0.0.0 --port 8000
```

**Party 1 — run the query:**

```bash
pip install pplp
```

```python
from pplp import Graph, compute_cn_remote, party2_client

graph1 = Graph.from_edge_list([("Alice", "Bob"), ("Alice", "Charlie")])

with party2_client("http://<party2-ip>:8000") as client:
    cn = compute_cn_remote(graph1, client, "Alice", "Dave")
    print(f"Common Neighbors: {cn}")
```

See the [Usage Guide](usage.md) for full details.
