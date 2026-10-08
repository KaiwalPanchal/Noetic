---
name: worker
description: Worker agent in a project repo, on its own branch, looping on tests.
trigger: on-demand
policy: loop
pipeline: delegate
prompt: delegate
budget:
  max_iterations: 3
tools: []
---
Worker agent that operates on a branch, executes tasks, and loops on tests.
