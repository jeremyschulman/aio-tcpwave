# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from typing import Optional, Sequence, Dict, Callable
import asyncio

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

from httpx import Response, ReadTimeout
from bidict import bidict

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from .client import TCPWaveClient


class TCPWaveObjectDetails(TCPWaveClient):
    """
    This mixin client is used to obtain object details, e.g., hostname
    """

    @TCPWaveClient.simple_api
    async def fetch_object_details(self, ip_address: str):
        """
        This returns the API record for the given IP Address.  The API
        record includes fields such as the name.

        Parameters
        ----------
        ip_address: str
            The IP address, for example "239.128.1.5"

        Returns
        -------
        HTTPx Response; the decorator will return the payload dictionary
        """
        return await self.get('/home/getObjectDetails', params=dict(ipAddress=ip_address))
