from __future__ import annotations
from contextlib import contextmanager

import httpx


@contextmanager
def party2_client(base_url: str, timeout: float = 30.0):
    """Context manager returning an httpx.Client for Party 2's server.

    Usage:
        with party2_client("http://192.168.1.10:8000") as client:
            result = compute_cn_remote(graph1, client, "A", "E")
    """
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        yield client
