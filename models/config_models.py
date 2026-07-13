"""Typed representations of the workflow configuration file.

These dataclasses mirror the structure of config/workflow.json so the
rest of the app works with typed objects rather than raw dictionaries.
ConfigService is responsible for constructing them from parsed JSON.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Country:
    """A country available for vendor onboarding.

    Attributes:
        name: Display name, e.g. "France". Used as the selection key.
        documents: Document types required for this country, in order.
    """

    name: str
    documents: list[str]


@dataclass(frozen=True)
class ProcessStep:
    """A single stage in the simulated onboarding process.

    Attributes:
        id: Stable identifier, e.g. "extract". Used in state, not shown.
        title: Human-readable label shown on the progress card.
    """

    id: str
    title: str


@dataclass(frozen=True)
class WorkflowConfig:
    """The fully parsed workflow configuration.

    Attributes:
        countries: Countries keyed by display name for O(1) lookup.
        operations: Available operation labels, in display order.
        process: Ordered process steps driving the simulation.
        step_delay_seconds: Delay between simulated steps.
    """

    countries: dict[str, Country]
    operations: list[str]
    process: list[ProcessStep]
    step_delay_seconds: float = 2.0

    def get_country(self, name: str) -> Country | None:
        """Return the country by display name, or None if absent.

        Args:
            name: The country display name to look up.

        Returns:
            The matching Country, or None if no such country exists.
        """
        return self.countries.get(name)