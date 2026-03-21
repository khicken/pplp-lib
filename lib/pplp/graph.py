from __future__ import annotations
from collections import defaultdict


class Graph:
    def __init__(self):
        self._adj: dict[str, set[str]] = defaultdict(set)

    def add_edge(self, u: str, v: str):
        self._adj[u].add(v)
        self._adj[v].add(u)

    def neighbors(self, node: str) -> set[str]:
        return set(self._adj.get(node, set()))

    def has_edge(self, u: str, v: str) -> bool:
        return v in self._adj.get(u, set())

    def local_intersection(self, x: str, y: str) -> set[str]:
        return self.neighbors(x) & self.neighbors(y)

    @classmethod
    def from_edge_list(cls, edges: list[tuple[str, str]]) -> Graph:
        g = cls()
        for u, v in edges:
            g.add_edge(u, v)
        return g
