# Local-First Software: You Own Your Data, in spite of the Cloud

By Martin Kleppmann, Adam Wiggins, Peter van Hardenberg, and Mark McGranaghan (Ink & Switch, 2019)

## The Seven Ideals of Local-First Systems

Cloud computing gave us real-time collaboration at the expense of user agency, data longevity, and offline capability. When a cloud service shuts down or internet connectivity drops on a flight, the user is locked out of their own thoughts and records. Local-first software reconciles the best aspects of cloud collaboration with the durability and autonomy of personal computing.

A system qualifies as local-first when it satisfies seven structural ideals:
1. **No spinners: your work at your fingertips.** Read and write operations must execute immediately against the local disk without waiting for a remote roundtrip.
2. **Your work is not trapped on one device.** Seamless multi-device synchronization is continuous and transparent.
3. **The network is optional.** Every core feature functions completely offline, during intermittent connectivity, and on high-latency links.
4. **Seamless collaboration with others.** Multiple users can simultaneously edit shared documents without locking mechanisms.
5. **The long now.** Data created today must remain readable and editable thirty years from now, even if the original vendor goes out of business.
6. **Security and privacy by default.** End-to-end encryption ensures user documents are unreadable by cloud intermediaries.
7. **You retain ultimate ownership and control.** The user's device holds the authoritative, primary copy of data; cloud servers act strictly as replication relays and archival backups, never as the single source of truth.

## Technical Primitives: CRDTs and State Convergence

To achieve seamless multi-master collaboration without centralized write arbiters, local-first architectures employ Conflict-free Replicated Data Types (CRDTs) or append-only deterministic operational logs. When network partitions heal, peers exchange delta vectors and converge deterministically to the identical document state.

## Core Heuristic

- **When architecting client-server synchronization** → Prioritize **Local storage as primary copy and CRDTs for convergence** over _Centralized database as single source of truth_ because local-first guarantees continuous offline availability and perpetual user data ownership. (Rule: `Local disk is primary truth; cloud servers are ephemeral replication relays`) [Tier 2] [Tags: distributed-systems, architecture]
