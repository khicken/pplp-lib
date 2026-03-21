# Protocol Details

This page explains the cryptographic protocol implemented by PPLP, based on [Demirag/Ayday et al. 2022](https://arxiv.org/abs/2210.01297).

## Problem

Two parties (Graph 1 and Graph 2) each hold a graph over partially overlapping node sets. Graph 1 wants to know: **how many common neighbors do nodes x and y have in the combined graph?** — without either party revealing their edges.

## Threat model

- **Semi-honest (honest-but-curious):** Both parties follow the protocol correctly but try to infer information from messages they receive.
- **Only Graph 1 learns the result.** Graph 2 learns nothing beyond the common public inputs (node identifiers x and y).
- **Node identifiers match** across graphs (e.g., both parties use email addresses).
- **x and y are not already direct neighbors** in either graph.

### What leaks

The basic protocol leaks intermediate intersection sizes (local2, crossover1, crossover2, overlap) to Graph 1. The paper shows this leakage is minimal for realistic graph sizes — see Section 3.3 of the paper for the full analysis.

A heavier variant using additively homomorphic encryption eliminates this leakage entirely (Section 4.1), but is not implemented here.

## The formula

Common Neighbors on the joint graph is decomposed as:

```
CN = local1 + local2 + crossover1 + crossover2 - overlap
```

Where:

| Term | Definition | How computed |
|------|-----------|-------------|
| `local1` | \|Γ₁(x) ∩ Γ₁(y)\| | Graph 1 computes locally |
| `local2` | \|Γ₂(x) ∩ Γ₂(y)\| | Graph 2 computes locally |
| `crossover1` | \|(Γ₁(x) \ local1) ∩ (Γ₂(y) \ local2)\| | PSI call #1 |
| `crossover2` | \|(Γ₁(y) \ local1) ∩ (Γ₂(x) \ local2)\| | PSI call #2 |
| `overlap` | \|local1_set ∩ local2_set\| | PSI call #3 |

The subtraction of `overlap` prevents double-counting nodes that appear in both local intersections.

## Step by step

### 1. Local preparation (each party independently)

Each party computes:

- Neighbor sets: Γ₁(x), Γ₁(y) for Graph 1; Γ₂(x), Γ₂(y) for Graph 2
- Local intersection: e.g., `local1_set = Γ₁(x) ∩ Γ₁(y)`
- **Remove** local intersection members from neighbor sets before PSI

The removal step is critical — without it, the crossover terms would double-count nodes already captured by the local terms.

### 2. Three PSI-cardinality calls

Each call uses [Private Set Intersection](https://en.wikipedia.org/wiki/Private_set_intersection) in **cardinality-only mode**: it reveals only the *size* of the intersection, not which elements are in it.

1. `crossover1 = PSI-CA(Γ₁(x) \ local1, Γ₂(y) \ local2)`
2. `crossover2 = PSI-CA(Γ₁(y) \ local1, Γ₂(x) \ local2)`
3. `overlap = PSI-CA(local1_set, local2_set)`

### 3. Combine

Graph 1 computes: `CN = local1 + local2 + crossover1 + crossover2 - overlap`

## Worked example

From the paper (Figure 6), with nodes A and E:

**Graph 1 (Alice):** A—B, A—C, A—G, A—H, E—C, E—D

**Graph 2 (Bob):** A—C, A—F, A—K, E—B, E—C, E—D, E—F

| Step | Computation | Result |
|------|------------|--------|
| local1 | Γ₁(A) ∩ Γ₁(E) | {C} → size 1 |
| local2 | Γ₂(A) ∩ Γ₂(E) | {C, F} → size 2 |
| Reduced Γ₁(A) | {H, G, B, C} \ {C} | {H, G, B} |
| Reduced Γ₁(E) | {C, D} \ {C} | {D} |
| Reduced Γ₂(A) | {C, F, K} \ {C, F} | {K} |
| Reduced Γ₂(E) | {B, C, D, F} \ {C, F} | {B, D} |
| crossover1 | \|{H,G,B} ∩ {B,D}\| | 1 |
| crossover2 | \|{D} ∩ {K}\| | 0 |
| overlap | \|{C} ∩ {C,F}\| | 1 |
| **CN** | 1 + 2 + 1 + 0 - 1 | **3** |

## PSI implementation

We use [OpenMined PSI](https://github.com/OpenMined/PSI) (`openmined-psi` on PyPI):

- ECDH-based protocol
- Cardinality-only mode (`reveal_intersection=False`)
- Golomb Coded Sets (GCS) for compressed representation
- C++ backend, pip-installable, supports macOS Apple Silicon and Linux
