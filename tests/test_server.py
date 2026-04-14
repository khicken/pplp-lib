import pytest
from pplp.server.session import PsiSession, SessionStore
from fastapi.testclient import TestClient
from pplp.graph import Graph
from pplp.server.app import create_app


def _paper_graph2():
    return Graph.from_edge_list([
        ("A", "C"), ("A", "F"), ("A", "K"),
        ("E", "B"), ("E", "C"), ("E", "D"), ("E", "F"),
    ])


def test_prepare_returns_session_and_local2():
    app = create_app(_paper_graph2())
    client = TestClient(app)
    resp = client.post("/prepare", json={"x": "A", "y": "E"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["local2"] == 2          # {C, F}
    assert "session_id" in data


def test_prepare_does_not_leak_direct_edge():
    # Security: server must not reveal whether x-y is a direct edge in graph2.
    # Response shape must match the no-edge case.
    g2 = Graph.from_edge_list([("A", "E")])
    app = create_app(g2)
    client = TestClient(app)
    resp = client.post("/prepare", json={"x": "A", "y": "E"})
    assert resp.status_code == 200
    data = resp.json()
    assert "direct_link" not in data
    assert "session_id" in data and data["session_id"]


def test_store_creates_and_retrieves_session():
    store = SessionStore()
    session = PsiSession(
        sets={"crossover1": {"a", "b"}, "crossover2": {"c"}, "overlap": {"d"}},
        local2=2,
    )
    sid = store.put(session)
    assert store.get(sid) is session


def test_store_returns_none_for_unknown_id():
    store = SessionStore()
    assert store.get("nonexistent") is None


def test_store_delete_removes_session():
    store = SessionStore()
    sid = store.put(PsiSession(sets={}, local2=0))
    store.delete(sid)
    assert store.get(sid) is None


import base64
import private_set_intersection.python as psi
from private_set_intersection.proto.psi_python_proto_pb.private_set_intersection.proto.psi_pb2 import ServerSetup, Response


def _get_session(client, x="A", y="E"):
    resp = client.post("/prepare", json={"x": x, "y": y})
    return resp.json()["session_id"]


def test_psi_setup_returns_base64_setup():
    app = create_app(_paper_graph2())
    client = TestClient(app)
    sid = _get_session(client)

    resp = client.post(f"/psi/{sid}/setup", json={"call": "crossover1", "client_set_size": 3})
    assert resp.status_code == 200
    setup = ServerSetup.FromString(base64.b64decode(resp.json()["setup"]))
    # GCS structure was requested — verify it was used
    assert setup.HasField("gcs")


def test_psi_respond_returns_correct_intersection_count():
    # crossover1: Party 2 has g2_y = {B, D} (E's neighbors excl. local2={C,F})
    # Party 1 sends g1_x = {H, G, B} (A's neighbors in g1 excl. local1={C})
    # Intersection = {B} → count == 1
    app = create_app(_paper_graph2())
    client = TestClient(app)
    sid = _get_session(client)

    psi_client = psi.client.CreateWithNewKey(reveal_intersection=False)
    setup_resp = client.post(f"/psi/{sid}/setup", json={"call": "crossover1", "client_set_size": 3})
    setup = ServerSetup.FromString(base64.b64decode(setup_resp.json()["setup"]))

    request = psi_client.CreateRequest(["H", "G", "B"])
    request_b64 = base64.b64encode(request.SerializeToString()).decode()
    respond_resp = client.post(f"/psi/{sid}/respond", json={"call": "crossover1", "request": request_b64})
    assert respond_resp.status_code == 200

    response = Response.FromString(base64.b64decode(respond_resp.json()["response"]))
    count = psi_client.GetIntersectionSize(setup, response)
    assert count == 1  # only B is shared


def test_psi_setup_unknown_session_returns_404():
    app = create_app(_paper_graph2())
    client = TestClient(app)
    resp = client.post("/psi/bad-id/setup", json={"call": "crossover1", "client_set_size": 1})
    assert resp.status_code == 404


def test_psi_setup_invalid_call_returns_422():
    app = create_app(_paper_graph2())
    client = TestClient(app)
    sid = _get_session(client)
    resp = client.post(f"/psi/{sid}/setup", json={"call": "invalid_call", "client_set_size": 1})
    assert resp.status_code == 422


def test_psi_respond_without_setup_returns_400():
    app = create_app(_paper_graph2())
    client = TestClient(app)
    sid = _get_session(client)
    request_b64 = base64.b64encode(b"fake").decode()
    resp = client.post(f"/psi/{sid}/respond", json={"call": "crossover1", "request": request_b64})
    assert resp.status_code == 400


import os
import tempfile
from pplp.server.app import load_graph_from_csv


def test_load_graph_from_csv():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("A,B\nB,C\nA,C\n")
        path = f.name
    try:
        g = load_graph_from_csv(path)
        assert g.has_edge("A", "B")
        assert g.has_edge("B", "C")
        assert g.has_edge("A", "C")
    finally:
        os.unlink(path)
