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


def parse_edges(text: str) -> list[tuple[str, str]]:
    edges = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.replace(",", " ").split()
        if len(parts) >= 2:
            u, v = parts[0].strip(), parts[1].strip()
            if u and v and u != v:
                edge = tuple(sorted([u, v]))
                if edge not in edges:
                    edges.append(edge)
    return edges


def get_nodes_from_edges() -> list[str]:
    nodes = set()
    for u, v in st.session_state.edges:
        nodes.add(u)
        nodes.add(v)
    return sorted(nodes)


def render_graph_builder():
    st.subheader("Graph Builder")

    col_graph, col_edges = st.columns([2, 1])

    with col_edges:
        st.text_area(
            "Edges (one per line: A,B or A B)",
            height=500,
            placeholder="Alice,Bob\nBob,Charlie\nAlice,Charlie",
            key="edge_text",
        )
        st.session_state.edges = parse_edges(st.session_state.edge_text or "")

    with col_graph:
        if st.session_state.edges:
            render_graph_viz()
            nodes = get_nodes_from_edges()
            st.markdown(
                f"<p style='text-align: center; color: gray;'>{len(nodes)} nodes, {len(st.session_state.edges)} edges</p>",
                unsafe_allow_html=True,
            )
        else:
            st.info("Add edges to see visualization")


def render_graph_viz():
    try:
        from pyvis.network import Network
        import streamlit.components.v1 as components

        net = Network(height="500px", width="100%", bgcolor="#ffffff", font_color="#000000")
        net.barnes_hut(
            gravity=-3000,
            central_gravity=0.3,
            spring_length=120,
            spring_strength=0.05,
            damping=0.09,
        )

        nodes = set()
        for u, v in st.session_state.edges:
            nodes.add(u)
            nodes.add(v)

        for node in nodes:
            net.add_node(node, label=node, size=25,
                         font={"size": 14, "face": "arial"},
                         color={"background": "#4CAF50", "border": "#388E3C",
                                "highlight": {"background": "#81C784", "border": "#4CAF50"},
                                "hover": {"background": "#81C784", "border": "#4CAF50"}})

        for u, v in st.session_state.edges:
            net.add_edge(u, v, width=2,
                         color={"color": "#666666",
                                "highlight": "#81C784",
                                "hover": "#81C784"})

        net.set_options("""
        {
            "interaction": {
                "hover": true,
                "zoomView": true,
                "dragView": true,
                "navigationButtons": false
            },
            "physics": {
                "stabilization": {"iterations": 200}
            }
        }
        """)

        html = net.generate_html()
        # Inject a fullscreen toggle button
        fullscreen_btn = """
        <style>
            body { margin: 0; }
            .fullscreen-btn {
                position: absolute;
                top: 8px;
                right: 8px;
                z-index: 9999;
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                cursor: pointer;
                font-size: 13px;
                font-family: arial, sans-serif;
                opacity: 0.85;
            }
            .fullscreen-btn:hover { opacity: 1; }
            body:fullscreen, body:-webkit-full-screen {
                background: #ffffff;
            }
            body:fullscreen #mynetwork, body:-webkit-full-screen #mynetwork {
                width: 100vw !important;
                height: 100vh !important;
            }
        </style>
        <button class="fullscreen-btn" onclick="
            var el = document.body;
            if (!document.fullscreenElement) {
                el.requestFullscreen();
                this.textContent = 'Exit Fullscreen';
            } else {
                document.exitFullscreen();
                this.textContent = 'Fullscreen';
            }
        ">Fullscreen</button>
        """
        html = html.replace("<body>", "<body>" + fullscreen_btn)
        components.html(html, height=520, scrolling=False)
    except ImportError:
        st.warning("Install pyvis for interactive visualization: uv pip install pyvis")
        st.code("\n".join(f"{u} -- {v}" for u, v in st.session_state.edges))


def build_graph_from_session():
    from pplp import Graph
    g = Graph()
    for u, v in st.session_state.edges:
        g.add_edge(u, v)
    return g


LOCALTUNNEL_HEADERS = {"Bypass-Tunnel-Reminder": "true"}


def test_party2_connection(party2_url: str):
    """Test connection to Party 2's server."""
    import httpx

    try:
        with httpx.Client(base_url=party2_url, timeout=15, headers=LOCALTUNNEL_HEADERS) as client:
            resp = client.get("/health")
            if resp.status_code == 200:
                st.success("Connected to Party 2's server!")
                st.info(
                    "Your setup looks good. Run a query below to compute Common Neighbors. "
                    "A result of 0 means the node pair has no common neighbors across both graphs."
                )
            elif resp.status_code == 404:
                st.error(
                    "Connected to the tunnel, but the server isn't responding. "
                    "This can happen if localtunnel's splash page is blocking requests. "
                    "Make sure Party 2 has the latest code with the bypass header."
                )
            else:
                st.error(f"Unexpected response: HTTP {resp.status_code}")
    except httpx.ConnectError:
        st.error("Connection failed. Check that Party 2's server is running and the URL is correct.")
    except httpx.ReadTimeout:
        st.error("Connection timed out. The tunnel may be slow or Party 2's server may not be responding.")
    except Exception as e:
        st.error(f"Connection failed: {e}")


def start_localtunnel(port: int) -> tuple[subprocess.Popen | None, str | None]:
    try:
        process = subprocess.Popen(
            ["lt", "--port", str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        import re
        url_pattern = re.compile(r"https://\S+")
        deadline = time.time() + 15

        while time.time() < deadline:
            if process.poll() is not None:
                return None, None
            line = process.stdout.readline()
            if not line:
                time.sleep(0.1)
                continue
            match = url_pattern.search(line)
            if match:
                return process, match.group()
        process.terminate()
        return None, None
    except FileNotFoundError:
        return None, None


def start_server_with_tunnel(graph, port: int = 8765):
    import uvicorn
    from pplp.server.app import create_app

    app = create_app(graph)

    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="warning")
    server = uvicorn.Server(config)

    server_ready = threading.Event()

    def run_server():
        old_startup = server.startup

        async def patched_startup(**kwargs):
            await old_startup(**kwargs)
            server_ready.set()

        server.startup = patched_startup
        server.run()

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    if not server_ready.wait(timeout=10):
        return None, None, None

    tunnel_process, tunnel_url = start_localtunnel(port)
    if tunnel_url is None:
        if tunnel_process:
            tunnel_process.terminate()
        return server_thread, None, None

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

            if server_thread is None:
                st.error(f"Server failed to start on port {port}. The port may already be in use.")
                return

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
                st.info(f"Server is running locally at http://localhost:{port}. "
                        "You can share this address directly if both machines are on the same network.")
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
    3. Query for link prediction scores between node pairs
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
            test_party2_connection(party2_url)

    st.markdown("---")
    st.subheader("Run PPLP Query")

    if not st.session_state.edges:
        st.warning("Add edges to your graph first.")
        return

    if not party2_url:
        st.warning("Enter Party 2's server URL above.")
        return

    nodes = get_nodes_from_edges()

    measure = st.radio(
        "Link prediction measure",
        options=["Common Neighbors", "Jaccard"],
        horizontal=True,
        help="Common Neighbors = raw count of shared neighbors. "
             "Jaccard = CN normalized by total neighbors (0–1 range). "
             "Jaccard uses 2 extra PSI calls for degree computation.",
    )

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
                label = "Compute " + measure
                if st.button(label, type="primary"):
                    run_pplp_query(party2_url, graph1, node_x, node_y, measure)


def run_pplp_query(party2_url: str, graph1, x: str, y: str, measure: str = "Common Neighbors"):
    from pplp import compute_cn_remote, compute_jaccard_remote, party2_client

    use_jaccard = measure == "Jaccard"
    label = "Jaccard" if use_jaccard else "Common Neighbors"

    with st.spinner(f"Computing {label} for ({x}, {y})..."):
        try:
            with party2_client(party2_url, timeout=60.0) as client:
                if use_jaccard:
                    result = compute_jaccard_remote(graph1, client, x, y)
                else:
                    result = compute_cn_remote(graph1, client, x, y)

            if use_jaccard:
                st.success(f"Jaccard score for ({x}, {y}): **{result:.4f}**")
            else:
                st.success(f"Common Neighbors score for ({x}, {y}): **{result}**")

            if result == 0:
                st.markdown(f"""
                **Interpretation:** No common neighbors were found across both graphs for ({x}, {y}).
                This can mean:
                - Node `{x}` or `{y}` may not exist in Party 2's graph
                - The nodes exist but share no neighbors across the combined graph
                - Only one party has a neighbor to both nodes

                This is a valid result, not an error.
                """)
            else:
                if use_jaccard:
                    st.markdown("""
                    **Interpretation:**
                    - Jaccard ranges from 0 to 1 — higher means more neighbor overlap relative to total neighbors
                    - Normalizes for node degree, unlike raw Common Neighbors
                    - Computed with 5 PSI calls without revealing graph structure
                    """)
                else:
                    st.markdown("""
                    **Interpretation:**
                    - Higher scores indicate stronger likelihood of a future link
                    - This score was computed without either party revealing their graph structure
                    """)

        except Exception as e:
            st.error(f"Error during computation: {e}")


def main():
    st.title("Privacy-Preserving Link Prediction (PPLP)")

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
