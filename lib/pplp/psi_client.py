from __future__ import annotations
import base64

import private_set_intersection.python as psi
from private_set_intersection.proto.psi_python_proto_pb.private_set_intersection.proto.psi_pb2 import ServerSetup, Response as PsiResponse

_FPR = 0.001


def remote_psi_cardinality(
    http_client,
    client_set: set[str],
    session_id: str,
    call: str,
) -> int:
    """Perform one PSI-cardinality call against Party 2's server.

    Args:
        http_client: An httpx.Client pointed at Party 2's base URL,
                     or a FastAPI TestClient (same interface).
        client_set:  Party 1's set for this PSI call.
        session_id:  Session ID returned by POST /prepare.
        call:        One of "crossover1", "crossover2", "overlap".
    """
    if not client_set:
        return 0

    psi_client = psi.client.CreateWithNewKey(reveal_intersection=False)
    client_list = list(client_set)

    setup_resp = http_client.post(
        f"/psi/{session_id}/setup",
        json={"call": call, "client_set_size": len(client_list)},
    )
    setup_resp.raise_for_status()
    setup = ServerSetup.FromString(base64.b64decode(setup_resp.json()["setup"]))

    request = psi_client.CreateRequest(client_list)
    request_b64 = base64.b64encode(request.SerializeToString()).decode()
    respond_resp = http_client.post(
        f"/psi/{session_id}/respond",
        json={"call": call, "request": request_b64},
    )
    respond_resp.raise_for_status()
    response = PsiResponse.FromString(base64.b64decode(respond_resp.json()["response"]))

    return psi_client.GetIntersectionSize(setup, response)
