# Deep Modules: Designing for High Depth over Shallow Interfaces

By John Ousterhout (*A Philosophy of Software Design*, 2018)

## 1. Deep vs. Shallow Modules

The most fundamental goal in software design is the minimization of cognitive complexity. A module is a unit of software, such as a class, a package, or a subsystem, that consists of an interface and an implementation. The interface consists of everything that a developer using the module must know in order to use it. The implementation consists of the code that carries out the promises made by the interface.

Modules can be characterized by their depth:
- A **deep module** is one whose interface is simple, minimal, and compact, yet the implementation behind that interface provides substantial, powerful functionality. Deep modules maximize the benefit of information hiding: users of the module need to understand only a tiny surface area, while vast internal complexities (caching, locking, buffering, protocol negotiation) remain hidden. Examples of deep modules include standard Unix file I/O (`open`, `read`, `write`, `close`), garbage collectors, and deterministic compilers.
- A **shallow module** is one whose interface is complicated relative to the small amount of functionality it provides. Shallow modules do not hide complexity; they merely displace it. An interface with 25 configuration knobs and 15 public methods that simply passes data to an internal dictionary provides almost no design leverage.

## 2. Interface Minimization and Information Hiding

The best classes and public interfaces are those that do a great deal of work while demanding very little from their callers:
- Keep the number of public methods small (ideally 3 to 5 core methods).
- Keep method parameter lists lean and concise; do not leak internal implementation choices or configuration parameters through method arguments.
- Provide sensible, deterministic defaults for all internal mechanisms so callers only specify domain essentials.

## 3. Directional Heuristic

- **When designing public interfaces and library boundaries** → Prioritize **Deep modules with minimal public interfaces** over _Shallow modules exposing internal configuration knobs_ because compact interfaces minimize caller cognitive load and allow implementations to evolve independently. (Rule: `Expose at most 3-5 high-leverage public methods hiding internal complexity`) [Tier 2] [Tags: software-design, architecture]
