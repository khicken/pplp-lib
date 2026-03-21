# pplp — Development

## Setup

```bash
uv sync --all-extras
```

## Run tests

```bash
uv run pytest               # all tests
uv run pytest tests/test_graph.py -v   # single file
uv run pytest -k "paper"    # by keyword
```

## Project structure

```
lib/pplp/
    __init__.py      # public API: Graph, compute_cn, DirectLinkFound
    graph.py         # Graph class (adjacency list, neighbor queries)
    psi.py           # PSI cardinality wrapper (openmined-psi)
    protocol.py      # compute_cn — Ayday et al. protocol orchestration
tests/
    test_graph.py
    test_psi.py
    test_protocol.py
```

## Docs

```bash
uv run mkdocs serve          # preview at http://127.0.0.1:8000
uv run mkdocs gh-deploy      # deploy to GitHub Pages
```
