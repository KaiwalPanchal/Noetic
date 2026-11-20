# Choose Boring Technology

By Dan McKinley (2015)

## The Problem with Novelty

The appetite of engineering teams for novelty is virtually unlimited, whereas their operational capacity to understand and maintain novel technologies in production is strictly constrained. When teams introduce new technologies into their core production infrastructure, they inevitably invite "unknown unknowns"—modes of failure, performance degradation, and operational quirks that can only be discovered through painful, late-night production emergencies.

Boring technology does not mean bad technology. Boring technology means technology whose failure modes are thoroughly understood, documented, and reproducible. Postgres is boring. Linux is boring. Memcached is boring. When Postgres encounters a deadlock, thousands of engineers have encountered the exact same deadlock over the past twenty years; a solution is a single search away.

## The Innovation Token Budget

Every company or engineering organization starts with a finite, scarce budget: **innovation tokens**. A typical engineering team possesses approximately **two to three innovation tokens** to spend across their entire operational stack.

When you choose to write your backend in an esoteric language, you spend one innovation token. When you replace a standard relational database with a distributed graph database or bespoke event-sourcing engine, you spend another innovation token. When you swap reliable asynchronous task queues for an unproven streaming broker, you spend your third innovation token.

Once your innovation token budget is exhausted, you have zero margin for error. If your core product problem requires a genuine technical breakthrough, you are bankrupt. Therefore:

- **When choosing core infrastructure** → Prioritize **Well-understood, established technologies** over _Novel, cutting-edge tools_ because the operational cost of unknown unknowns far exceeds initial feature benefits. (Rule: `Budget at most two innovation tokens for the entire company stack`) [Tier 2] [Tags: architecture, infrastructure]
- **Governing Invariant:** Unbudgeted technical novelty directly increases production failure frequency.

## Boundary Flip Conditions

The rule is not absolute dogma; it is an economic discipline. You are permitted to spend an innovation token if and only if the novel technology provides an order-of-magnitude competitive advantage directly tied to your core business proposition. If you are building a global search index, you may need a custom distributed storage layer. If you are building an internal CRUD inventory tool for a four-person team, choosing Kafka, event sourcing, and a distributed graph database is reckless negligence.
