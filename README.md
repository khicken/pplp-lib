# pplp-lib

Privacy-preserving link prediction library for two-party distributed graphs, based on [Demirag/Ayday et al. 2022](https://arxiv.org/abs/2210.01297). For CWRU's CSDS 356/456, Spring 2026.

Compute Common Neighbors across two graphs without either party revealing their edges — using Private Set Intersection (PSI) under the hood.

```python
from pplp import Graph, compute_cn

graph1 = Graph.from_edge_list([("A", "B"), ("A", "C")])
graph2 = Graph.from_edge_list([("A", "D"), ("B", "D")])

cn = compute_cn(graph1, graph2, "A", "D")
```

**[Documentation](https://khicken.github.io/pplp-lib/)**
