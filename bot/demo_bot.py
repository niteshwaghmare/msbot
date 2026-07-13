"""Concrete bot class: the composition root for the demo.

Builds the configuration, controller, and router, wiring them together
and handing the router to the activity handler it extends.
"""

from __future__ import annotations

from bot.activity_handler import DemoActivityHandler
from bot.card_router import CardRouter
from bot.workflow_controller import WorkflowController
from services.config_service import ConfigService


class DemoBot(DemoActivityHandler):
    """The Vendor Onboarding demo bot and its object graph."""

    def __init__(
        self,
        config_path: str = "config/workflow.json",
        app_id: str = "",
    ) -> None:
        """Construct the bot and all its collaborators.

        Args:
            config_path: Path to the workflow configuration file.
            app_id: The bot's Microsoft App Id, needed for background
                progress-card updates. Empty is fine for the Emulator.
        """
        config = ConfigService(config_path)
        controller = WorkflowController(config, app_id=app_id)
        router = CardRouter(controller)
        super().__init__(router)