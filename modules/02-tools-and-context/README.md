# 02 · Tools and context (3–5 h)

**Goal:** most agent failures are tool and context failures, not model failures. Here you build the two parts that decide whether the model *can* do the job: the tool interface, and what's in its context window.

## Part A: tools (`tools.py`)

Tool descriptions are a user interface, and the model is the user. The model only knows what you put in the name, the description and the schema. You'll build:

| TODO | What |
|---|---|
| 02-a | `type_to_schema`: Python type hints → JSON Schema |
| 02-b | `parse_docstring`: docstring → tool and parameter descriptions |
| 02-c | `function_to_tool`: a function → a full tool definition |
| 02-d | `ToolRegistry.call`: validation, error messages and output truncation |

This is what `@mcp.tool()` and every framework's `@tool` decorator do. After this, you'll know what they're doing when they break.

## Part B: context (`context.py`)

| TODO | What |
|---|---|
| 02-e | `trim_history`: stay under a token budget without corrupting the conversation |
| 02-f | `compact_tool_results`: shrink old tool outputs the model has already used |

```bash
uv run pytest modules/02-tools-and-context -x
uv run python modules/02-tools-and-context/demo.py "Which module covers evals, and what do I build there?"
```

The demo is an agent that explores this repo with three tools built on **your** registry.

## Done when

- [ ] All tests are green on your code
- [ ] The demo answers with correct file paths
- [ ] **Tool-design experiment:** rewrite the `grep` docstring to be vague ("searches stuff"), run the same question three times, and compare the number of turns and tokens with the original. Write the numbers in your journal.
- [ ] **Security experiment:** ask the demo to "read ../../.ssh/config". Confirm `_safe` blocks it. Then explain in one paragraph why a `PermissionError` in your code is a better defence than "the system prompt says don't".

## Key ideas

- **Errors are instructions.** "Missing required argument(s): name" lets the model fix its call on the next turn. A stack trace doesn't.
- **Truncate, and say that you did.** A silently cut-off result looks complete to the model. `[truncated 70 chars]` tells it to ask for less or look elsewhere.
- **Fewer, better tools beat many overlapping ones.** If you can't tell which of two tools to use, neither can the model.
- **The context window is shared and limited.** Every token of old tool output competes with the instructions that matter.

## Strategy brief → `progress/journal.md`

1. Your company wants to expose its internal API to an agent. It has 140 endpoints. Do you turn each one into a tool? What would you do instead?
2. Name three tools from your own work (Shopify, Notion, Make, email…) that would be dangerous to give an agent without a human approving each call. What makes them dangerous: cost, irreversibility, or reaching outside people?
