import argparse
import os

import click
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from recipes.executor import RecipeAgentExecutor

PUBLIC = "0.0.0.0"

card = AgentCard(
    name="Recipe Agent",
    description="Suggests recipes from what is in the fridge.",
    url="https://recipes.example.com/",
    version="1.0.0",
    capabilities=AgentCapabilities(streaming=True),
    default_input_modes=["text"],
    default_output_modes=["text"],
    skills=[AgentSkill(id="suggest", name="Suggest a recipe", description="", tags=["food"])],
)
handler = DefaultRequestHandler(agent_executor=RecipeAgentExecutor(), task_store=InMemoryTaskStore())
server = A2AStarletteApplication(agent_card=card, http_handler=handler)

# ruleid: a2a-server-without-auth
uvicorn.run(server.build(), host="0.0.0.0", port=9999)

app = server.build()
# ruleid: a2a-server-without-auth
uvicorn.run(app, host=PUBLIC, port=9999)

# ruleid: a2a-server-without-auth
uvicorn.run(app, host="::", port=9999)

HOST = os.environ.get("RECIPES_HOST", "0.0.0.0")
# ruleid: a2a-server-without-auth
config = uvicorn.Config(app, host=HOST, port=9999)

SERVE = {"host": "0.0.0.0", "port": 9999}
# ruleid: a2a-server-without-auth
uvicorn.run(app, **SERVE)


def serve(host: str = "0.0.0.0", port: int = 9999) -> None:
    # ruleid: a2a-server-without-auth
    uvicorn.run(app, host=host, port=port)


def cli() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()
    # ruleid: a2a-server-without-auth
    uvicorn.run(app, host=args.host, port=9999)


@click.command()
@click.option("--host", "host", default="0.0.0.0")
@click.option("--port", "port", default=9999)
def main(host: str, port: int) -> None:
    # ruleid: a2a-server-without-auth
    uvicorn.run(app, host=host, port=port)


# uvicorn's default host is 127.0.0.1.
# ok: a2a-server-without-auth
uvicorn.run(app, port=9999)

# ok: a2a-server-without-auth
uvicorn.run(app, host="127.0.0.1", port=9999)


def serve_local(host: str = "localhost") -> None:
    # ok: a2a-server-without-auth
    uvicorn.run(app, host=host, port=9999)


# Not a bind: comparing against the wildcard address.
if HOST == "0.0.0.0":
    # ok: a2a-server-without-auth
    uvicorn.run(app, host="127.0.0.1", port=9999)
