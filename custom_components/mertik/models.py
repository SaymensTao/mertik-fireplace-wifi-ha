from enum import Enum
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


class StoveState(str, Enum):
    OFF = "off"
    STARTING = "starting"
    IGNITING = "igniting"
    RUNNING = "running"
    MODULATING = "modulating"
    STOPPING = "stopping"
    ERROR = "error"
    UNAVAILABLE = "unavailable"


class CommandStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    TIMED_OUT = "timed_out"


@dataclass
class StoveCommand:
    name: str
    issued_at: datetime
    expected_state: StoveState
    timeout: int
    status: CommandStatus = CommandStatus.PENDING
