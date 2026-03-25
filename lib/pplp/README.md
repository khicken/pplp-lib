# pplp — Development

## Setup

```bash
uv sync --all-extras
```

## Run tests

```bash
# run all tests
uv run pytest

# run one test
uv run pytest tests/test_graph.py -v
```

## Project structure

```bash
lib/pplp/
    __init__.py        # public API: Graph, compute_cn, compute_cn_remote, DirectLinkFound, party2_client
    graph.py           # Graph class (adjacency list, neighbor queries)
    psi.py             # PSI cardinality wrapper (openmined-psi), local use
    psi_client.py      # remote_psi_cardinality — PSI over HTTP (Party 1 side)
    protocol.py        # compute_cn (local) and compute_cn_remote (distributed)
    client.py          # party2_client — httpx context manager for Party 1
    server/
        __init__.py
        app.py         # create_app factory, load_graph_from_csv, pplp-server CLI
        routes.py      # Party 2 FastAPI endpoints: /prepare, /psi/{id}/setup, /psi/{id}/respond
        session.py     # PsiSession dataclass + SessionStore
tests/
    test_graph.py
    test_psi.py
    test_protocol.py
    test_server.py
    test_psi_client.py
    test_protocol_remote.py
```

## Docs

```bash
uv run mkdocs serve
uv run mkdocs gh-deploy
```
