# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from .client import TCPWaveClient


class TCPWaveSearch(TCPWaveClient):
    """
    This mixin is used to execute the "Entity Global Search".

    Notes
    -----
    Does not appear to function properly when using SSL certification
    authentication. The TCPWave responds with a 500.  Going to leave in here
    for now until we can get further clarity from TCPWave.
    """

    async def search(self, expression: str):
        return await self.post(
            "/search/search",
            params={
                "search_term": expression,
                "search_type": "Text",
                "entity_type": "object",
            },
        )
