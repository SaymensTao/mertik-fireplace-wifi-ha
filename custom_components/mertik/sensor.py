from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MertikCoordinator
from .models import StoveState, CommandStatus

_LOGGER = logging.getLogger(__name__)


SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="status",
        name="Fireplace Status",
        icon="mdi:fire",
    ),
    SensorEntityDescription(
        key="command",
        name="Fireplace Last Command",
        icon="mdi:console-line",
    ),
    SensorEntityDescription(
        key="command_state",
        name="Fireplace Command State",
        icon="mdi:progress-clock",
    ),
    SensorEntityDescription(
        key="last_update",
        name="Fireplace Last Update",
        icon="mdi:clock-outline",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mertik fireplace sensors."""
    coordinator: MertikCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            MertikFireplaceSensor(coordinator, entry, description)
            for description in SENSORS
        ]
    )


class MertikFireplaceSensor(
    CoordinatorEntity[MertikCoordinator], SensorEntity
):
    """Sensor exposing fireplace state and command telemetry."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MertikCoordinator,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._attr_unique_id = (
            f"{entry.entry_id}_{description.key}"
        )

    # -------------------------
    # Sensor values
    # -------------------------

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        desc = self.entity_description.key
        coord = self.coordinator
        cmd = coord.last_command

        if desc == "status":
            return coord.current_state.value

        if desc == "command":
            return cmd.name if cmd else "idle"

        if desc == "command_state":
            return cmd.status.value if cmd else CommandStatus.CONFIRMED.value

        if desc == "last_update":
            return (
                datetime.now(timezone.utc).isoformat()
                if coord.last_update_success
                else None
            )

        return None

    # -------------------------
    # Availability
    # -------------------------

    @property
    def available(self) -> bool:
        """Sensor is unavailable only if coordinator is unavailable."""
        return (
            self.coordinator.current_state
            != StoveState.UNAVAILABLE
        )

    # -------------------------
    # Extra attributes
    # -------------------------

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Extra debugging attributes."""
        coord = self.coordinator
        cmd = coord.last_command

        attrs = {
            "connection_state": (
                "connected"
                if coord.last_update_success
                else "disconnected"
            ),
            "poll_interval_seconds": coord.update_interval.total_seconds(),
        }

        if cmd:
            attrs.update(
                {
                    "command_issued_at": cmd.issued_at.isoformat(),
                    "command_timeout": cmd.timeout,
                    "command_elapsed": round(
                        (
                            datetime.utcnow() - cmd.issued_at
                        ).total_seconds(),
                        1,
                    ),
                }
            )

        return attrs
