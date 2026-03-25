from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PsiSession:
    sets: dict[str, set[str]]     # call -> Party 2's neighbor set for that call
    local2: int                    # |Γ₂(x) ∩ Γ₂(y)| — revealed to Party 1 per protocol
    servers: dict[str, Any] = field(default_factory=dict)  # call -> psi.server object


class SessionStore:
    def __init__(self):
        self._store: dict[str, PsiSession] = {}

    def put(self, session: PsiSession) -> str:
        sid = str(uuid.uuid4())
        self._store[sid] = session
        return sid

    def get(self, session_id: str) -> PsiSession | None:
        return self._store.get(session_id)

    def delete(self, session_id: str) -> None:
        self._store.pop(session_id, None)
