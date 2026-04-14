from __future__ import annotations
import base64
from typing import Literal

import private_set_intersection.python as psi
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from private_set_intersection.proto.psi_python_proto_pb.private_set_intersection.proto.psi_pb2 import Request as PsiRequest

from pplp.server.session import PsiSession

_FPR = 0.001
_DATA_STRUCTURE = psi.DataStructure.GCS
CallType = Literal["crossover1", "crossover2", "overlap", "degree_x", "degree_y"]

router = APIRouter()


# --- /health ---

class HealthResponse(BaseModel):
    status: str


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok")


# --- /prepare ---

class PrepareRequest(BaseModel):
    x: str
    y: str
    measure: Literal["cn", "jaccard"] = "cn"


class PrepareResponse(BaseModel):
    local2: int
    session_id: str
    degree2_x: int = 0
    degree2_y: int = 0


@router.post("/prepare", response_model=PrepareResponse)
def prepare(req: PrepareRequest, request: Request):
    g2 = request.app.state.graph
    store = request.app.state.store

    x, y = req.x, req.y
    local2_set = g2.local_intersection(x, y)
    g2_x = g2.neighbors(x) - local2_set
    g2_y = g2.neighbors(y) - local2_set

    sets = {
        "crossover1": g2_y,
        "crossover2": g2_x,
        "overlap":    local2_set,
    }

    degree2_x = 0
    degree2_y = 0
    if req.measure == "jaccard":
        sets["degree_x"] = g2.neighbors(x)
        sets["degree_y"] = g2.neighbors(y)
        degree2_x = len(g2.neighbors(x))
        degree2_y = len(g2.neighbors(y))

    session = PsiSession(sets=sets, local2=len(local2_set))
    sid = store.put(session)
    return PrepareResponse(
        local2=session.local2,
        session_id=sid,
        degree2_x=degree2_x,
        degree2_y=degree2_y,
    )


# --- /psi/{session_id}/setup and /psi/{session_id}/respond ---

class PsiSetupRequest(BaseModel):
    call: CallType
    client_set_size: int


class PsiSetupResponse(BaseModel):
    setup: str      # base64 ServerSetup


class PsiRespondRequest(BaseModel):
    call: CallType
    request: str    # base64 Request


class PsiRespondResponse(BaseModel):
    response: str   # base64 Response


@router.post("/psi/{session_id}/setup", response_model=PsiSetupResponse)
def psi_setup(session_id: str, req: PsiSetupRequest, request: Request):
    store = request.app.state.store
    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    party2_set = list(session.sets[req.call])
    server = psi.server.CreateWithNewKey(reveal_intersection=False)
    setup = server.CreateSetupMessage(_FPR, req.client_set_size, party2_set, _DATA_STRUCTURE)
    session.servers[req.call] = server

    return PsiSetupResponse(setup=base64.b64encode(setup.SerializeToString()).decode())


@router.post("/psi/{session_id}/respond", response_model=PsiRespondResponse)
def psi_respond(session_id: str, req: PsiRespondRequest, request: Request):
    store = request.app.state.store
    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    server = session.servers.get(req.call)
    if server is None:
        raise HTTPException(status_code=400, detail=f"Setup not called for call '{req.call}'")

    request_proto = PsiRequest.FromString(base64.b64decode(req.request))
    response = server.ProcessRequest(request_proto)
    return PsiRespondResponse(response=base64.b64encode(response.SerializeToString()).decode())
