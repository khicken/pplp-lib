"""
PPLP Streamlit App - Privacy-Preserving Link Prediction

Two-party UI for building graphs and running the Common Neighbors protocol.
Each party runs this app locally and connects via localtunnel.
"""
from __future__ import annotations

import subprocess
import threading
import time
from typing import TYPE_CHECKING

import streamlit as st

if TYPE_CHECKING:
    import httpx

st.set_page_config(page_title="PPLP - Privacy-Preserving Link Prediction", layout="wide")


def init_session_state():
    if "edges" not in st.session_state:
        st.session_state.edges = []
    if "server_running" not in st.session_state:
        st.session_state.server_running = False
    if "tunnel_url" not in st.session_state:
        st.session_state.tunnel_url = None
    if "server_thread" not in st.session_state:
        st.session_state.server_thread = None
    if "tunnel_process" not in st.session_state:
        st.session_state.tunnel_process = None


init_session_state()


def get_nodes_from_edges() -> list[str]:
    nodes = set()
    for u, v in st.session_state.edges:
        nodes.add(u)
        nodes.add(v)
    return sorted(nodes)


def render_graph_builder():
    st.subheader("Graph Builder")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Add Edge**")
        with st.form("add_edge_form", clear_on_submit=True):
            edge_input = st.text_input(
                "Edge (format: A,B or A B)",
                placeholder="e.g., Alice,Bob",
                help="Enter two node names separated by comma or space",
            )
            if st.form_submit_button("Add Edge"):
                edge_input = edge_input.strip()
                if edge_input:
                    parts = edge_input.replace(",", " ").split()
                    if len(parts) >= 2:
                        u, v = parts[0].strip(), parts[1].strip()
                        if u and v and u != v:
                            edge = tuple(sorted([u, v]))
                            if edge not in st.session_state.edges:
                                st.session_state.edges.append(edge)
                                st.rerun()
                            else:
                                st.warning("Edge already exists")
                        else:
                            st.error("Invalid edge: nodes must be different and non-empty")
                    else:
                        st.error("Please enter two node names")

    with col2:
        st.markdown("**Bulk Import (CSV)**")
        uploaded_file = st.file_uploader(
            "Upload edge list CSV", type=["csv", "txt"], help="One edge per line: nodeA,nodeB"
        )
        if uploaded_file is not None:
            import io
            content = uploaded_file.read().decode("utf-8")
            lines = content.strip().split("\n")
            new_edges = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                parts = line.replace(",", " ").split()
                if len(parts) >= 2:
                    u, v = parts[0].strip(), parts[1].strip()
                    if u and v and u != v:
                        edge = tuple(sorted([u, v]))
                        if edge not in st.session_state.edges and edge not in new_edges:
                            new_edges.append(edge)
            if new_edges:
                st.session_state.edges.extend(new_edges)
                st.success(f"Added {len(new_edges)} edges")
                st.rerun()

    st.markdown("---")

    col_graph, col_edges = st.columns([2, 1])

    with col_edges:
        st.markdown("**Current Edges**")
        if st.session_state.edges:
            for i, (u, v) in enumerate(st.session_state.edges):
                col_e, col_x = st.columns([3, 1])
                col_e.text(f"{u} -- {v}")
                if col_x.button("X", key=f"del_{i}", help="Remove edge"):
                    st.session_state.edges.pop(i)
                    st.rerun()

            if st.button("Clear All Edges", type="secondary"):
                st.session_state.edges = []
                st.rerun()
        else:
            st.info("No edges yet. Add edges above.")

    with col_graph:
        st.markdown("**Graph Visualization**")
        if st.session_state.edges:
            render_graph_viz()
        else:
            st.info("Add edges to see visualization")

    st.markdown("---")
    nodes = get_nodes_from_edges()
    st.markdown(f"**Summary:** {len(nodes)} nodes, {len(st.session_state.edges)} edges")


def render_graph_viz():
    try:
        import networkx as nx
        import matplotlib.pyplot as plt

        G = nx.Graph()
        G.add_edges_from(st.session_state.edges)

        fig, ax = plt.subplots(figsize=(8, 6))
        pos = nx.spring_layout(G, seed=42)
        nx.draw(
            G,
            pos,
            ax=ax,
            with_labels=True,
            node_color="#4CAF50",
            node_size=700,
            font_size=10,
            font_weight="bold",
            edge_color="#666666",
            width=2,
        )
        ax.set_title("Your Graph")
        st.pyplot(fig)
        plt.close(fig)
    except ImportError:
        st.warning("Install networkx and matplotlib for visualization: uv sync --extra ui")
        st.code("\n".join(f"{u} -- {v}" for u, v in st.session_state.edges))


def build_graph_from_session():
    from pplp import Graph
    g = Graph()
    for u, v in st.session_state.edges:
        g.add_edge(u, v)
    return g


def start_localtunnel(port: int) -> subprocess.Popen | None:
    try:
        process = subprocess.Popen(
            ["lt", "--port", str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        for line in iter(process.stdout.readline, ""):
            if "your url is:" in line.lower():
                url = line.strip().split()[-1]
                return process, url
            if "https://" in line.lower():
                for word in line.split():
                    if word.startswith("https://"):
                        return process, word
        return process, None
    except FileNotFoundError:
        return None, None


def start_server_with_tunnel(graph, port: int = 8765):
    import uvicorn
    from pplp.server.app import create_app

    app = create_app(graph)

    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="warning")
    server = uvicorn.Server(config)

    def run_server():
        server.run()

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    time.sleep(1)

    result = start_localtunnel(port)
    if result[0] is None:
        return server_thread, None, None

    tunnel_process, tunnel_url = result
    return server_thread, tunnel_process, tunnel_url


def render_party2_mode():
    st.header("Party 2 Mode (Server)")
    st.markdown("""
    As Party 2, you will:
    1. Build your private graph below
    2. Start the PPLP server with a public tunnel URL
    3. Share the URL with Party 1
    """)

    render_graph_builder()

    st.markdown("---")
    st.subheader("Server Control")

    if not st.session_state.edges:
        st.warning("Add edges to your graph before starting the server.")
        return

    if not st.session_state.server_running:
        port = st.number_input("Server Port", value=8765, min_value=1024, max_value=65535)

        if st.button("Start Server with Tunnel", type="primary"):
            graph = build_graph_from_session()

            with st.spinner("Starting server and tunnel..."):
                server_thread, tunnel_process, tunnel_url = start_server_with_tunnel(graph, port)

            st.session_state.server_thread = server_thread
            st.session_state.tunnel_process = tunnel_process

            if tunnel_url:
                st.session_state.tunnel_url = tunnel_url
                st.session_state.server_running = True
                st.rerun()
            else:
                st.error(
                    "Failed to start localtunnel. Make sure it's installed: `npm install -g localtunnel`"
                )
                st.info(f"Server is running locally at http://localhost:{port}")
    else:
        st.success("Server is running!")

        st.markdown("### Share this URL with Party 1:")
        st.code(st.session_state.tunnel_url, language=None)

        st.info(
            "Keep this window open. Party 1 will connect using the URL above to run PPLP queries."
        )

        if st.button("Stop Server", type="secondary"):
            if st.session_state.tunnel_process:
                st.session_state.tunnel_process.terminate()
            st.session_state.server_running = False
            st.session_state.tunnel_url = None
            st.session_state.tunnel_process = None
            st.rerun()


def render_party1_mode():
    st.header("Party 1 Mode (Client)")
    st.markdown("""
    As Party 1, you will:
    1. Build your private graph below
    2. Connect to Party 2's server URL
    3. Query for Common Neighbors between node pairs
    """)

    render_graph_builder()

    st.markdown("---")
    st.subheader("Connect to Party 2")

    party2_url = st.text_input(
        "Party 2 Server URL",
        placeholder="https://xxx.loca.lt",
        help="Enter the tunnel URL shared by Party 2",
    )

    if party2_url:
        if st.button("Test Connection"):
            try:
                import httpx
                with httpx.Client(base_url=party2_url, timeout=10) as client:
                    resp = client.get("/")
                    st.success(f"Connected! Server responded with status {resp.status_code}")
            except Exception as e:
                st.error(f"Connection failed: {e}")

    st.markdown("---")
    st.subheader("Run PPLP Query")

    if not st.session_state.edges:
        st.warning("Add edges to your graph first.")
        return

    if not party2_url:
        st.warning("Enter Party 2's server URL above.")
        return

    nodes = get_nodes_from_edges()

    col1, col2 = st.columns(2)
    with col1:
        node_x = st.selectbox("Node X", options=nodes, index=0 if nodes else None)
    with col2:
        node_y = st.selectbox("Node Y", options=nodes, index=min(1, len(nodes) - 1) if nodes else None)

    if node_x and node_y:
        if node_x == node_y:
            st.error("Please select two different nodes")
        else:
            graph1 = build_graph_from_session()

            if graph1.has_edge(node_x, node_y):
                st.warning(f"{node_x} and {node_y} are already direct neighbors in your graph!")
            else:
                if st.button("Compute Common Neighbors", type="primary"):
                    run_pplp_query(party2_url, graph1, node_x, node_y)


def run_pplp_query(party2_url: str, graph1, x: str, y: str):
    from pplp import compute_cn_remote, DirectLinkFound, party2_client

    with st.spinner(f"Computing Common Neighbors for ({x}, {y})..."):
        try:
            with party2_client(party2_url, timeout=60.0) as client:
                result = compute_cn_remote(graph1, client, x, y)

            st.success(f"Common Neighbors score for ({x}, {y}): **{result}**")

            st.markdown("""
            **Interpretation:**
            - Higher scores indicate stronger likelihood of a future link
            - This score was computed without either party revealing their graph structure
            """)

        except DirectLinkFound:
            st.warning(
                f"**Direct link found!** Nodes {x} and {y} are already connected in Party 2's graph. "
                "This is stronger evidence than Common Neighbors."
            )
        except Exception as e:
            st.error(f"Error during computation: {e}")


def main():
    st.title("PPLP - Privacy-Preserving Link Prediction")

    st.markdown("""
    This tool enables two parties to compute **Common Neighbors** link prediction
    scores without revealing their private graph structures.
    """)

    st.sidebar.title("Role Selection")
    role = st.sidebar.radio(
        "Select your role:",
        options=["Party 1 (Client)", "Party 2 (Server)"],
        help="Party 2 starts the server; Party 1 connects and initiates queries",
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    **How it works:**
    1. Party 2 builds their graph and starts server
    2. Party 2 shares the tunnel URL with Party 1
    3. Party 1 builds their graph and connects
    4. Party 1 queries for Common Neighbors
    5. Result is computed using PSI (Private Set Intersection)
    """)

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Requirements:**")
    st.sidebar.code("npm install -g localtunnel", language="bash")

    if role == "Party 2 (Server)":
        render_party2_mode()
    else:
        render_party1_mode()


if __name__ == "__main__":
    main()
