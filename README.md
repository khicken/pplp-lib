# pplp-lib

Privacy-preserving link prediction library for two-party distributed graphs, based on [Demirag/Ayday et al. 2022](https://arxiv.org/abs/2210.01297). For CWRU's CSDS 356/456, Spring 2026.

Compute Common Neighbors across two graphs without either party revealing their edges — using Private Set Intersection (PSI) under the hood.

## Quick start

### Web UI

```bash
uv sync --extra ui
npm install -g localtunnel
uv run streamlit run app.py
```

Party 2 starts the server and shares the tunnel URL. Party 1 connects and runs queries.

### Python API

```python
from pplp import Graph, compute_cn_remote, party2_client

graph1 = Graph.from_edge_list([("A", "B"), ("A", "C")])

with party2_client("https://<party2-tunnel-url>") as client:
    cn = compute_cn_remote(graph1, client, "A", "D")
    print(f"Common Neighbors: {cn}")
```

**[Documentation](https://khicken.github.io/pplp-lib/)**
