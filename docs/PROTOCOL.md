# Protocol sketch

```mermaid
flowchart TD
  R[Reliability scores] --> T[k trust tiers]
  T --> Q[Quorum of 2f+1, high tiers first]
  T --> P[Primary rotates inside top tier]
  P --> PRE[PRE-PREPARE with ML-DSA]
  PRE --> PR[PREPARE]
  PR --> C{2f+1 honest commits?}
  C -->|yes| D[Decide block]
  C -->|primary fault| E[Empty-block fallback and next view]
  S[Signature policy] -.-> PRE
```

Normal case is the classical three phases. View change is replaced by the empty-block vote described in the concept paper, which keeps the simulated message count at \(O(q^2)\) for quorum size \(q\).
