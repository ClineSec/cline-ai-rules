# The executor refuses callers that the context builder didn't authenticate.
import uvicorn
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication

from planner.wiring import card, handler_for


class PlannerExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue) -> None:
        if not context.call_context.user.is_authenticated:
            raise PermissionError("sign in first")


app = A2AStarletteApplication(agent_card=card, http_handler=handler_for(PlannerExecutor())).build()

# ok: a2a-server-without-auth
uvicorn.run(app, host="0.0.0.0", port=8080)
