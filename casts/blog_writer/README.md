
# Blog Writer Module

## Overview
This module defines the Blog Writer LangGraph graph responsible for running and extracting insights.

## Structure
```
blog_writer/
├── modules/
│   ├── agents.py      # Agents (optional)
│   ├── conditions.py  # Conditional logic (optional)
│   ├── models.py      # Models (optional)
│   ├── nodes.py       # Graph nodes (required)
│   ├── prompts.py     # Prompts (optional)
│   ├── state.py       # State definition (required)
│   ├── tools.py       # Tools (optional)
│   └── utils.py       # Utilities (optional)
├── pyproject.toml     # Package metadata
├── README.md          # This document
└── graph.py           # Graph definition
```

## Usage
```python
from casts.blog_writer.graph import blog_writer_graph

initial_state = {
    "query": "Hello, Act"
}

result = blog_writer_graph().invoke(initial_state)
```

## Extending
1. Add new node classes in `modules/nodes.py`
2. Define agents/conditions/tools/prompts/models if needed
3. Wire nodes into the graph in `graph.py`


