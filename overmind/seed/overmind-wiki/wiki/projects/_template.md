---
name: <project name>
status: active          # active | parked | blocked | done
goal: <goal page name>  # the goal this project serves (wiki/goals/)
competency: <competency page name>
repo: <path or URL, optional>
next_action: <the single next concrete step>
last_touched: YYYY-MM-DD
gate: <what must be true before this can move forward, or "none">
---

# <project name>

Registry page. One file per project, named after the project. The frontmatter above is the
registry: tools and agents read it to answer "what is in motion" and "what is stuck".

Keep the body short: intent, current state, links. History goes in `wiki/log/`.
