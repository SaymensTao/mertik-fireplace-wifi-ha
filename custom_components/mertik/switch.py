from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MertikCoordinator
from .models import StoveState

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Mertik fireplace switch from a config entry."""
    coordinator: MertikCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            MertikFireplaceSwitch(coordinator, entry),
        ]
    )


class MertikFireplaceSwitch(CoordinatorEntity[MertikCoordinator], SwitchEntity):
    """Representation of the fireplace power switch."""

    _attr_name = "Fireplace"
    _attr_icon = "mdi:fire"
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MertikCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the fireplace switch."""
        super().__init__(coordinator)

        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_fireplace_power"

    # -------------------------
    # State reporting
    # -------------------------

    @property
    def is_on(self) -> bool | None:
        """Return True if the fireplace is on.

        Intermediate states (STARTING, IGNITING, STOPPING)
        are considered 'on' so the UI does not flap.
        """
        state = self.coordinator.current_state

        if state == StoveState.UNAVAILABLE:
            return None

        return state not in (
            StoveState.OFF,
            StoveState.ERROR,
        )

    @property
    def available(self) -> bool:
        """Return if the entity is available."""
        return self.coordinator.current_state != StoveState.UNAVAILABLE

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose rich status for debugging and automations."""
        cmd = self.coordinator.last_command

        return {
            "stove_state": self.coordinator.current_state.value,
            "last_command": cmd.name if cmd else None,
            "command_status": cmd.status.value if cmd else "idle",
        }

    # -------------------------
    # Command handling
    # -------------------------

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the fireplace on.

        This is non-blocking and does not assume immediate success.
        """
        _LOGGER.info("User requested fireplace ON")

        await self.coordinator.async_send_command(
            command="POWER_ON",
            expected_state=StoveState.RUNNING,
            timeout=60,  # ignition can be slow
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the fireplace off.

        This is non-blocking and state-driven.
        """
        _LOGGER.info("User requested fireplace OFF")

        await self.coordinator.async_send_command(
            command="POWER_OFF",
            expected_state=StoveState.OFF,
            timeout=30,
        )
