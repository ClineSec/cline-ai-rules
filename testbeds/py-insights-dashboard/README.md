# py-insights-dashboard (testbed)

**Intentionally vulnerable.** A small Python analytics dashboard used to test `cline-ai-rules`
against Streamlit, Gradio, Panel, and Chainlit apps that render model output. Do not deploy it, run it,
or copy patterns from it.

The growth team's dashboard shows weekly KPIs and has an assistant that answers questions
about them. The Streamlit app is the main dashboard; `share.py` is the Gradio version handed
to stakeholders without dashboard access, and `explorer.py` is an older Panel page some
analysts still use. `assistant_chat.py` is the Chainlit chat embedded in the intranet page.

Nothing here needs network access to be scanned, and there are no real credentials. Expected
findings are listed in `expectations.yaml`.

## Layout

| Path | What it does |
| --- | --- |
| `insights/app.py` | Streamlit home page: KPI tiles and the analytics assistant chat |
| `insights/pages/1_Weekly_report.py` | Streamlit page: a model-written HTML report with a preview |
| `insights/pages/2_Anomalies.py` | Streamlit page: anomaly cards explained by Gemini |
| `insights/share.py` | Gradio Blocks app: assistant chat, weekly summary card, metric review |
| `insights/explorer.py` | Panel page: metric picker with a model-written narrative and a chat |
| `insights/formatting.py` | HTML snippets for tiles, cards, and chat bubbles |
| `insights/markdown_safety.py` | Strips images from model answers before they are shown |
| `insights/assistant_chat.py` | Chainlit chat for the analytics assistant (intranet embed) |
| `insights/pages/3_Metric_QA.py` | Streamlit page: a model-written metric definition and weekly read |
| `insights/pages/4_Answer_review.py` | Streamlit page: replays the session's analyst answers and grades the latest one |
| `insights/pages/4_Research_desk.py` | Streamlit page: the research desk chat, streamed from a pydantic-ai agent |
| `insights/research_desk.py` | The research desk's pydantic-ai agent and its KPI table tool |
| `insights/share_links.py` | Flask app serving read-only weekly summaries at `/r/<week>` |
| `insights/annotations.py` | Flask blueprint: KPI annotation search, export, and bulk delete over a Chroma collection shared by business units |
| `insights/report_search.py` | Flask blueprint: "similar weeks" search over past reports in a shared Pinecone index (LangChain) |
| `insights/anomaly_search.py` | Flask blueprint: past-anomaly search over a Milvus collection shared by business units |
| `insights/playbooks.py` | Flask blueprint: response-playbook search over MongoDB Atlas Vector Search (pymongo pipeline, LangChain) |
| `insights/digest.py`, `insights/templating.py` | Weekly KPI digest emails drafted by the model as a Jinja template |
| `insights/prompt_lab.py` | LangChain prompt lab for analyst prompts |
| `insights/prompt_store.py`, `insights/prompt_library.py` | Saved prompt chains (LangChain JSON in SQLite, LangSmith prompts) and the Flask blueprint where analysts import shared prompt exports |
| `insights/metrics.py` | KPI data and anomaly detection (pandas) |
| `insights/llm.py` | Model clients and prompts |
| `insights/a2a_agent.py`, `insights/a2a_finance.py`, `insights/partner_keys.py`, `insights/forecast_agent.py`, `insights/agent_cards/` | Insights agents for other teams' agents over A2A, the partner API keys the finance agent checks, and their agent cards |
| `insights/ops_copilot.py` | Growth ops copilot on the Responses API with hosted MCP servers (campaigns, a read-only warehouse, metric docs) |
| `insights/digest_agent.py` | Weekly digest agent (OpenAI Agents SDK) that mails the digest and links it in chat through hosted MCP servers, with approval callbacks |
| `insights/foundry_agent.py` | Finance-ops agent on Azure AI Foundry Agent Service (azure-ai-agents) with budget and ledger MCP servers |
| `insights/framework_agent.py` | Forecast review agent on Microsoft Agent Framework with hosted forecast and metrics MCP servers |
| `insights/analyst_agent.py` | LangChain v1 and deepagents analyst agents whose report tools pause for review through `interrupt_on` |
| `tests/` | pytest tests for the formatting and metrics helpers |
| `.qwen/settings.json`, `.qwen/.env` | Qwen Code setup for analysts: the team's coding model through the BI gateway, a Model Studio fallback, and telemetry kept on the laptop |

Run locally with `streamlit run insights/app.py`, `python -m insights.share`, or
`panel serve insights/explorer.py`, or `chainlit run insights/assistant_chat.py`.
