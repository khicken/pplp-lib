from __future__ import annotations
import csv

from fastapi import FastAPI

from pplp.graph import Graph
from pplp.server.session import SessionStore


def create_app(graph: Graph) -> FastAPI:
    app = FastAPI(title="PPLP Party 2 Server")
    app.state.graph = graph
    app.state.store = SessionStore()

    from pplp.server.routes import router
    app.include_router(router)

    return app


def load_graph_from_csv(path: str) -> Graph:
    """Load a graph from a two-column CSV (no header): one edge per row as 'u,v'."""
    edges = []
    with open(path, newline="") as f:
        for row in csv.reader(f):
            if len(row) >= 2:
                edges.append((row[0].strip(), row[1].strip()))
    return Graph.from_edge_list(edges)


def main():
    """CLI entrypoint: pplp-server <graph.csv> [--host HOST] [--port PORT]"""
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="Run the PPLP Party 2 server")
    parser.add_argument("graph_file", help="Path to edge-list CSV (u,v per line, no header)")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    graph = load_graph_from_csv(args.graph_file)
    app = create_app(graph)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
