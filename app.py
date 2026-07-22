"""Application entry point for the Vendor Onboarding demo bot.

Boots an aiohttp server exposing the Bot Framework messaging endpoint,
wires up the adapter with error handling, and dispatches incoming
activities to DemoBot.
"""

import sys
import traceback

from aiohttp import web
from aiohttp.web import Request, Response, json_response
from botbuilder.core import TurnContext
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.integration.aiohttp import CloudAdapter, ConfigurationBotFrameworkAuthentication
from botbuilder.schema import Activity

from bot.demo_bot import DemoBot

from config import BotConfig, DEFAULT_HOST, DEFAULT_PORT


# Adapter: authenticates and translates HTTP <-> Bot Framework activities.
ADAPTER = CloudAdapter(ConfigurationBotFrameworkAuthentication(BotConfig()))


async def on_error(context: TurnContext, error: Exception) -> None:
    """Adapter-level error handler.

    Logs the traceback and sends the user a friendly notice so a single
    failed turn does not surface as a silent hang.

    Args:
        context: The turn context in which the error occurred.
        error: The exception raised during turn processing.
    """
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()
    await context.send_activity("The bot hit an error. Please try again.")


ADAPTER.on_turn_error = on_error

# Single bot instance shared across requests.
BOT = DemoBot()


async def messages(req: Request) -> Response:
    """Handle an incoming activity POST from Teams / the Emulator.

    Args:
        req: The aiohttp request carrying a Bot Framework Activity as JSON.

    Returns:
        A 200/201 response, or the adapter's response for the turn.
    """
    if "application/json" not in req.headers.get("Content-Type", ""):
        return Response(status=415)

    body = await req.json()
    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    response = await ADAPTER.process_activity(auth_header, activity, BOT.on_turn)
    if response:
        return json_response(data=response.body, status=response.status)
    return Response(status=201)


def create_app() -> web.Application:
    """Build the aiohttp application with the messaging route.

    Returns:
        The configured aiohttp web application.
    """
    app = web.Application(middlewares=[aiohttp_error_middleware])
    app.router.add_post("/api/messages", messages)
    return app


APP = create_app()

if __name__ == "__main__":
    try:
        web.run_app(APP, host=DEFAULT_HOST, port=DEFAULT_PORT)
    except Exception as error:
        raise error
