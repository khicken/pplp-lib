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

### Option A: Web UI (recommended for getting started)

The easiest way to try PPLP is with the Streamlit app. Each party runs the app locally and connects via a public tunnel.

```bash
# Install with UI dependencies
uv sync --extra ui

# Install localtunnel (requires Node.js)
npm install -g localtunnel

# Run the app
uv run streamlit run app.py
```

**Party 2** selects "Party 2 (Server)", builds their graph, clicks "Start Server with Tunnel", and shares the URL.

**Party 1** selects "Party 1 (Client)", builds their graph, pastes Party 2's URL, and runs queries.

### Option B: Command line + Python

**Party 2 — start the server:**

```bash
uv sync
uv run pplp-server party2_graph.csv --tunnel
```

**Party 1 — run the query:**

```python
from pplp import Graph, compute_cn_remote, party2_client

graph1 = Graph.from_edge_list([("Alice", "Bob"), ("Alice", "Charlie")])

with party2_client("https://<party2-tunnel-url>") as client:
    cn = compute_cn_remote(graph1, client, "Alice", "Dave")
    print(f"Common Neighbors: {cn}")
```

See the [Usage Guide](usage.md) for full details.
