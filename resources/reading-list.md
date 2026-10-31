# Reading list, mapped to modules

**Rule: build first, read second.** Read an item *after* the module's tests are green. Then you're comparing someone else's approach with your own, not absorbing it passively.

## Primary sources (read these first)

| Module | Read | Why |
|---|---|---|
| 01, 05 | [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) (Anthropic) | The workflow-vs-agent spectrum and the patterns in Module 05 |
| 02 | [Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents) (Anthropic) | Tool design as a model-facing interface |
| 02 | [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) (Anthropic) | Why trimming and compaction matter, and the techniques beyond them |
| 01–02 | [Tool use docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools) (Claude API) | The exact protocol your loop speaks |
| 03 | [MCP specification](https://modelcontextprotocol.io/specification/latest) | Tools, resources, prompts, annotations, transports |
| 04 | [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) (Anthropic) | How eval suites for agents are built in practice |
| 05 | [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) (Anthropic) | A real orchestrator-workers system, with honest numbers on token cost |

## From the ProjectPro repo (the original "foundation"), triaged

These are vendor blog posts written partly to sell courses. They're useful for breadth and comparison, not as a core curriculum.
**Keep** = worth it after the module · **Skim** = for orientation only · **Skip** = outdated or low value

| Module | Article | Verdict |
|---|---|---|
| 01 | [How to Build an AI Agent from Scratch](https://www.projectpro.io/article/how-to-build-an-ai-agent-from-scratch/1072) | **Keep**: compare it with your loop |
| 01 | [How to Build an LLM Agent using OpenAI API](https://www.projectpro.io/article/llm-agents/1013) | Skim: same loop, different vendor |
| 01 | [AI Agent Architectures](https://www.projectpro.io/article/ai-agent-architectures/1135) | Skim |
| 01 | [Types of AI Agents](https://www.projectpro.io/article/types-of-ai-agents/1066) | Skip: textbook taxonomy (simple reflex, goal-based…) that predates LLM agents |
| 03 | [MCP Implementation with RAG](https://www.projectpro.io/article/mcp-with-rag/1144) | Skim: written against the MCP SDK 1.x (`FastMCP`) API |
| 03 | [MCP Projects](https://www.projectpro.io/article/mcp-projects/1142) | **Keep**: ideas for your own servers |
| 05 | [Agentic AI Design Patterns](https://www.projectpro.io/article/agentic-ai-design-patterns/1126) | **Keep**: cross-check against Module 05 |
| 05 | [How to Build Multi-Agent AI Systems](https://www.projectpro.io/article/multi-agent-ai/1083) | Skim |
| 05 | [How to Build Agentic Workflows](https://www.projectpro.io/article/agentic-workflows/1092) | Skim |
| 09 | [AI Agent Frameworks](https://www.projectpro.io/article/ai-agent-frameworks/1068) | **Keep**: landscape overview for framework selection |
| 07–08 | [LangChain vs LangGraph](https://www.projectpro.io/article/langchain-vs-langgraph/1123) | **Keep** if LangGraph is on your shortlist |
| 07–08 | [LangGraph Tutorial for Beginners](https://www.projectpro.io/article/langgraph/1109) | Keep if you pick LangGraph |
| 09 | [How to Build an AI Agent with Pydantic AI](https://www.projectpro.io/article/pydantic-ai/1088) | Keep if you pick Pydantic AI |
| 09 | [How to Build an AI Agent with CrewAI](https://www.projectpro.io/article/build-an-ai-agent-with-crewai/1095) | Keep if you pick CrewAI |
| 09 | [How to Build AI Agents with Phidata](https://www.projectpro.io/article/phidata-ai-agents/1090) | **Skip**: Phidata was renamed **Agno**, so read Agno's docs instead |
| 09 | [Microsoft AutoGen](https://www.projectpro.io/article/autogen/1139) | **Skip**: AutoGen is in maintenance mode; Microsoft points new users to **Microsoft Agent Framework** |
| 09 | [Agentic RAG with smolagents](https://www.projectpro.io/article/build-agentic-rags-with-smolagents/1094) | Skim |
| 09 | [AWS Bedrock Agents](https://www.projectpro.io/article/aws-bedrock-agents/1141) | Only if you're on AWS |
| 06 | [Build AI Agents using n8n](https://www.projectpro.io/article/how-to-build-ai-agents-with-n8n/1147) | **Keep**: pairs with Module 06 (read after you finish the linter, to see the canvas side) |
| — | [Conversational AI with RASA](https://www.projectpro.io/article/conversational-ai-with-rasa/1143) | Skip: intent-based chatbots, not LLM agents |
| — | [How Agentic AI Delivers ROI](https://www.projectpro.io/podcast/title/business-benefits-of-agentic-ai) | Skim for the strategy track, and check claims against your own numbers |
| — | Project-idea lists, interview Q&A, paid "projects" | Skip: your capstone is the project |

Statuses checked October 2026. Frameworks change quickly, so recheck before Module 09.
