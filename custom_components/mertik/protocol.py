class MertikProtocol:
    async def connect(self): ...
    async def close(self): ...
    async def send(self, command: str): ...
    async def poll_state(self) -> dict:
        """
        Return raw parsed state:
        {
            "power": True,
            "flame_level": 3,
            "error": None,
            ...
        }
        """
