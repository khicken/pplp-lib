# PPLP

**Privacy-Preserving Link Prediction** — a Python library enabling two-party Common Neighbors link prediction over distributed graphs without revealing private graph structure.

Based on [Demirag/Ayday et al. 2022](https://arxiv.org/abs/2210.01297).

## What it does

Two parties (each holding a graph) can compute how many common neighbors a pair of nodes has across their **combined** graph — without either party revealing their edges to the other. This is useful for:

- **Social networks** — friend recommendations across platforms
- **E-commerce** — collaborative product recommendations
- **Telecommunications** — targeted advertising across carriers
- **Bioinformatics** — cross-institutional disease/gene association

## How it works

The library uses [Private Set Intersection](https://en.wikipedia.org/wiki/Private_set_intersection) (PSI) to compute intersection **sizes** without revealing the intersections themselves. The Common Neighbors count is decomposed into local terms + crossover terms, requiring only 3 PSI calls per node pair.

## Quick start

```bash
pip install pplp
```

```python
from pplp import Graph, compute_cn

graph1 = Graph.from_edge_list([("A", "B"), ("A", "C"), ("B", "D")])
graph2 = Graph.from_edge_list([("A", "D"), ("C", "D")])

cn = compute_cn(graph1, graph2, "A", "D")
print(f"Common Neighbors: {cn}")
```

See the [Usage Guide](usage.md) for more details.
