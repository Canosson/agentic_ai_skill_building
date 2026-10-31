# 07 · LangGraph: state graphs (3–5 h)

**Goal:** rebuild the four Module 05 patterns as LangGraph graphs, so you can judge what a framework adds over plain Python, and what it costs. The model calls are identical. What changes is that the control flow becomes *data*: you can draw it, test it, and (in Module 08) checkpoint it.

> Prerequisite: Modules 01 and 05. If `patterns.py` isn't green yet, do that first, because here you're translating code you understand.

## Mental model

| Plain Python (05) | LangGraph (07) |
|---|---|
| Local variables | **State**: a `TypedDict` every node reads |
| A step in a function | **Node**: `fn(state) -> partial update` |
| `if` / `while` | **Conditional edge**: `fn(state) -> next node name` |
| `ThreadPoolExecutor` | **`Send`**: fan out to parallel nodes, merge with a **reducer** |
| The call stack | Gone. State is explicit, which is why it can be saved |

## Build (`graphs.py`)

| TODO | Graph | The new idea |
|---|---|---|
| 07-a | `build_chain_graph` | Building a graph dynamically from a list; a gate as a conditional edge |
| 07-b | `build_router_graph` | Conditional edges with a mapping; node names vs state keys |
| 07-c | `build_orchestrator_graph` | `Send` fan-out, reducers (`operator.add`), and why parallel results arrive in arbitrary order |
| 07-d | `build_refine_graph` | A **cycle** with a stop condition: the thing that's awkward as a chain and natural as a graph |

```bash
uv run pytest modules/07-langgraph-graphs -x
uv run python modules/07-langgraph-graphs/demo.py          # prints each graph as a Mermaid diagram + calls and tokens
```

Docs to keep open: [Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api) and [`Send`](https://docs.langchain.com/oss/python/langgraph/graph-api#send). The tests run on `FakeLLM`, so they're free and offline.

## Done when

- [ ] Tests green on your code
- [ ] You've pasted the Mermaid diagram of each graph into your journal (render it at mermaid.live) and can explain every edge
- [ ] **Parity experiment:** run Module 05's `evaluate_optimize` and this module's refine graph on the same task. Record calls and tokens for each. They should be near identical. If not, find out why.
- [ ] **Line count:** compare `patterns.py` against `graphs.py` for the same four patterns. Which is longer? Which is easier to *change* (say, adding a second critic)?
- [ ] **Reducer bug:** remove `Annotated[..., operator.add]` from `results` and run the orchestrator test. Write down what breaks and why.

## Key ideas

- **A graph is not smarter than a loop.** LangGraph adds no intelligence. It adds structure: explicit state, inspectable control flow, and persistence hooks.
- **Nodes return updates, not the whole state.** Return only the keys you changed. Mutating `state` in place is a bug waiting to happen.
- **Reducers decide what "parallel" means.** Without one, two workers writing the same key silently clobber each other (or LangGraph raises).
- **Order is not guaranteed across parallel branches.** Carry an index and sort, as 07-c does.
- **Cycles need an exit you can prove.** `max_rounds` in the edge function is the exit, not the critic's goodwill.

## Strategy brief → `progress/journal.md`

1. A teammate says "let's rewrite our working agent in LangGraph." What three things would you need to see in the current code or its failure history before agreeing?
2. Your graph has 11 nodes and 4 conditional edges. A newcomer needs to change one behaviour. Is that easier or harder than with 150 lines of plain Python? Defend your answer with your line-count experiment.
