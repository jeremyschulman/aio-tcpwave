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


class TCPWaveSubnets(TCPWaveClient):
    """
    This mixin client is used for subnet related actions
    """

    @TCPWaveClient.simple_api
    async def fetch_subnet_details(self, subnet: str):
        """
        This returns the API record about the given subnet.  The API
        record includes fields such as the name and subnet prefix-length
        value.

        Parameters
        ----------
        subnet: str
            The subnet IP address, for example "172.10.2.0"

        Returns
        -------
        HTTPx Response; the decorator will return the payload dictionary
        """
        return await self.get('/object/getSnAddr', params=dict(address=subnet))
