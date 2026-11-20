# Small Functions and Single-Responsibility Decomposition

By Robert C. Martin (*Clean Code: A Handbook of Agile Software Craftsmanship*, 2008)

## 1. The Small Functions Mandate

The first rule of functions is that they should be small. The second rule of functions is that they should be smaller than that. Functions should rarely be 20 lines long, and hardly ever 100 lines long. Functions should ideally be 4 to 8 lines in length, doing exactly one thing and doing it well.

When a function does only one thing, its intent is immediately transparent to the reader. Large monolithic functions with high cyclomatic complexity, multiple levels of nested loops, and mixed abstraction layers are the primary cause of software bugs.

## 2. Extraction and Level of Abstraction

To achieve extreme smallness, code must be aggressively decomposed:
- Every block within an `if`, `else`, `while`, or `for` statement should be exactly one line long: typically a call to an extracted helper function.
- This not only keeps the enclosing function tiny, but also adds documentary value because the function called within the block can have a nicely descriptive name.
- Statements within a function should all be at the same level of abstraction. Mixing high-level business concepts with low-level string manipulation or buffer management in the same method creates severe cognitive dissonance.

## 3. Directional Heuristic

- **When authoring procedural and operational methods** → Prioritize **Aggressive decomposition into tiny, single-purpose functions** over _Consolidated multi-responsibility procedures_ because tiny functions isolate side effects and enable comprehensive unit testing. (Rule: `Keep functions under 10 lines and decompose every sub-operation into a dedicated helper`) [Tier 2] [Tags: clean-code, refactoring]
