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
    """CLI entrypoint: pplp-server <graph.csv> [--host HOST] [--port PORT] [--tunnel]"""
    import argparse
    import threading

    import uvicorn

    parser = argparse.ArgumentParser(description="Run the PPLP Party 2 server")
    parser.add_argument("graph_file", help="Path to edge-list CSV (u,v per line, no header)")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--tunnel",
        action="store_true",
        help="Expose server via ngrok tunnel (no firewall config needed)",
    )
    args = parser.parse_args()

    graph = load_graph_from_csv(args.graph_file)
    app = create_app(graph)

    config = uvicorn.Config(app, host=args.host, port=args.port, log_level="info")
    server = uvicorn.Server(config)

    if args.tunnel:
        from pyngrok import ngrok

        tunnel = ngrok.connect(args.port, bind_tls=True)
        public_url = tunnel.public_url

        print("\n" + "=" * 60)
        print("  TUNNEL READY")
        print("  Share this URL with Party 1:")
        print(f"  {public_url}")
        print("=" * 60 + "\n")

    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()
    server_thread.join()


if __name__ == "__main__":
    main()
