from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from datetime import timedelta, datetime
import asyncio
import logging

from .protocol import MertikProtocol
from .models import StoveState, StoveCommand, CommandStatus

_LOGGER = logging.getLogger(__name__)

class MertikCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, host):
        self.hass = hass
        self.protocol = MertikProtocol(host)
        self.current_state = StoveState.UNAVAILABLE
        self.last_command: StoveCommand | None = None
        self._lock = asyncio.Lock()

        super().__init__(
            hass,
            _LOGGER,
            name="Mertik Stove",
            update_interval=timedelta(seconds=30),
        )
##Polling logic##
async def _async_update_data(self):
    try:
        async with self._lock:
            raw = await self.protocol.poll_state()
            self._update_state(raw)
            self._resolve_command_if_needed()
            return raw
    except Exception as err:
        raise UpdateFailed(err)
 ##State derivation##   
def _update_state(self, raw: dict):
    if raw.get("error"):
        self.current_state = StoveState.ERROR
    elif not raw.get("power"):
        self.current_state = StoveState.OFF
    elif raw.get("igniting"):
        self.current_state = StoveState.IGNITING
    else:
        self.current_state = StoveState.RUNNING
##Command Queue with Confirmation##
async def async_send_command(
    self,
    command: str,
    expected_state: StoveState,
    timeout: int = 30,
):
    async with self._lock:
        self.last_command = StoveCommand(
            name=command,
            issued_at=datetime.utcnow(),
            expected_state=expected_state,
            timeout=timeout,
        )

        _LOGGER.info("Sending command %s", command)
        await self.protocol.send(command)

        # Poll more frequently while command is active
        self.update_interval = timedelta(seconds=3)
        await self.async_request_refresh()
##Command resolution logic##
def _resolve_command_if_needed(self):
    cmd = self.last_command
    if not cmd:
        return

    elapsed = (datetime.utcnow() - cmd.issued_at).total_seconds()

    if self.current_state == cmd.expected_state:
        cmd.status = CommandStatus.CONFIRMED
        self._finalize_command()

    elif elapsed > cmd.timeout:
        cmd.status = CommandStatus.TIMED_OUT
        self._finalize_command()
##Finalizing command##
def _finalize_command(self):
    _LOGGER.info(
        "Command %s %s",
        self.last_command.name,
        self.last_command.status,
    )

    self.update_interval = timedelta(seconds=30)
