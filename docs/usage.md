# Usage Guide

## Installation

```bash
uv sync
```

For the web UI, include the `ui` extra:

```bash
uv sync --extra ui
npm install -g localtunnel
```

### Platform support

| Platform | Status |
|----------|--------|
| macOS (Apple Silicon) | Fully supported |
| Linux (x86_64) | Fully supported |
| Windows | Use WSL2 or Docker (see below) |

The `openmined-psi` package only provides pre-built wheels for macOS ARM64 and Linux x86_64. Windows users have two options:

#### Option 1: WSL2 (recommended)

Install [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install) with Ubuntu, then run PPLP inside WSL:

```bash
# In WSL terminal
cd /mnt/c/path/to/pplp-lib
uv sync --extra ui
uv run streamlit run app.py
```

#### Option 2: Docker

```bash
docker run -it --rm -p 8501:8501 -v $(pwd):/app -w /app python:3.12 bash
pip install uv && uv sync --extra ui
uv run streamlit run app.py --server.address 0.0.0.0
```

Then open `http://localhost:8501` in your browser.

---

## Web UI (Streamlit App)

The Streamlit app provides a visual interface for building graphs and running PPLP — no Python code required.

```bash
uv run streamlit run app.py
```

### Party 2: Start the server

1. Open the app and select **"Party 2 (Server)"** in the sidebar
2. Build your graph using the Graph Builder:
    - Type edges like `Alice,Bob` or `Alice Bob` and click "Add Edge"
    - Or upload a CSV file with one edge per line
3. Click **"Start Server with Tunnel"**
4. Copy the tunnel URL (e.g., `https://xyz.loca.lt`) and share it with Party 1
5. Keep the app running while Party 1 sends queries

### Party 1: Run queries

1. Open the app and select **"Party 1 (Client)"** in the sidebar
2. Build your graph using the Graph Builder
3. Paste Party 2's tunnel URL and click **"Test Connection"** to verify
4. Select the node pair (X, Y) you want to query
5. Click **"Compute Common Neighbors"**

The result shows the Common Neighbors score computed privately — neither party reveals their graph structure.

---

## Command Line Usage

For scripting or automation, use the CLI and Python API directly.

### Setup

Each party installs `pplp` independently on their own machine. Node IDs must match across both graphs (e.g., both use email addresses or phone numbers for shared nodes).

### Party 2: Start the server

Party 2 prepares a CSV edge list (no header, one edge per line) and starts the server:

```
Alice,Bob
Alice,Charlie
Bob,Dave
```

#### Option 1: ngrok tunnel (no firewall config)

Use `--tunnel` to expose the server via ngrok:

```bash
uv run pplp-server party2_graph.csv --tunnel
```

The server prints a public URL (e.g., `https://abc123.ngrok.io`) — share this with Party 1. No router config or port forwarding needed. Use `--tunnel-timeout` if on a slow connection (default: 60s).

> **Note:** Free ngrok accounts assign a random URL each time. For a stable URL, sign up at ngrok.com and add your authtoken.

#### Option 2: Manual firewall

If you prefer to open ports yourself:

```bash
uv run pplp-server party2_graph.csv --host 0.0.0.0 --port 8000
```

Options:

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | `0.0.0.0` | Bind address |
| `--port` | `8000` | Port |
| `--tunnel` | `False` | Expose via ngrok tunnel |
| `--tunnel-timeout` | `60` | Tunnel connection timeout (seconds) |

### Party 1: Run the query

Party 1 builds their graph in Python and connects to Party 2's server:

```python
from pplp import Graph, compute_cn_remote, party2_client

graph1 = Graph.from_edge_list([
    ("Alice", "Bob"), ("Alice", "Charlie"), ("Alice", "Grace"), ("Alice", "Henry"),
    ("Eve", "Charlie"), ("Eve", "Diana"),
])

with party2_client("https://<party2-tunnel-url>") as client:
    cn = compute_cn_remote(graph1, client, "Alice", "Eve")
    print(f"Common Neighbors: {cn}")
```

Only Party 1 learns the result. Party 2's graph structure is never revealed.

---

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
from pplp import DirectLinkFound

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

---

## What's happening under the hood

For a candidate pair (x, y), `compute_cn_remote` runs the Demirag/Ayday et al. protocol over HTTP:

1. Party 1 calls `/prepare` — Party 2 checks for a direct link and returns its local intersection size
2. Three **PSI-cardinality** calls (each a pair of HTTP round-trips to `/psi/{id}/setup` and `/psi/{id}/respond`) reveal only the *sizes* of crossover intersections
3. Party 1 combines: `CN = local1 + local2 + crossover1 + crossover2 - overlap`

No raw neighbor sets are ever exchanged. See [Protocol Details](protocol.md) for the full breakdown.
