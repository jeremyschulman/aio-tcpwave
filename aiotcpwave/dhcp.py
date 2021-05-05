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


class TCPWaveDCHP(TCPWaveClient):
    """
    This TCPWave client mixin provides DCHP related features, most importantly
    finding active DHCP lease records.
    """

    def __init__(self, *vargs, **kwargs):
        super(TCPWaveDCHP, self).__init__(*vargs, **kwargs)
        self.dhcp_servers = bidict()

    async def fetch_dhcp_servers(self, **params):
        """
        This method is used to fetch the list of configured DHCP servers.  As a result
        of executing this method the `dhcp_servers` dictionary is populated for use
        by the other "find" methods.

        Other Parameters
        ----------------
        Any parameters supported by the underlying /dhcpservers/list API

        Returns
        -------
        List of DHCP server records (dict) from TCPWave API.
        """
        res = await self.get(
            "/dhcpserver/list", params=params or dict(orgName=self.tcpwave_org)
        )
        res.raise_for_status()
        body = res.json()
        self.dhcp_servers.clear()
        self.dhcp_servers.update({rec["name"]: rec["v4_ipaddress"] for rec in body})
        return body

    async def fetch_dhcp_leases(self, servers: Optional[Sequence[str]] = None):
        """
        This method is used to generate the active DHCP leases found in
        the provided list of servers; or all servers if none provided.

        Parameters
        ----------
        servers: list of dhcp server nams

        Yields
        ------
        DHCP lease record (dict)
        """
        gen = self._fetch_dhcp_leases_tasker(servers=servers)

        # pull the tasks from the generator; but they are not used.
        _ = await gen.__anext__()

        async for rec in gen:
            yield rec

    async def find_dhcp_lease_ipaddr(
        self, ipaddr: str, servers: Optional[Sequence[str]] = None
    ) -> Optional[Dict]:
        """
        This coroutine is used to find the first (only) DHCP lease record with a matching
        IP address address value.

        Parameters
        ----------
        ipaddr: str
            The IPv4 address to find

        servers:
            Optional list of DHCP server names.  If not provided, then all
            avaialble DHCP servers will be checked.

        Returns
        -------
        The matching DHCP lease record if found, or None.
        """
        gen = self._fetch_dhcp_leases_tasker(servers=servers)
        tasks = await gen.__anext__()

        rec: dict
        async for rec in gen:
            if rec["address"] == ipaddr:
                found = rec
                break
        else:
            return None

        for t in tasks:
            t.cancel()

        found["dhcpServerName"] = self.dhcp_servers.inv[rec["dhcpServer"]]  # noqa
        return found

    async def find_dhcp_lease_macaddr(
        self, macaddr: str, servers: Optional[Sequence[str]] = None
    ) -> Optional[Dict]:
        """
        This coroutine is used to find the first (only) DHCP lease record with a matching
        MAC address value.

        Parameters
        ----------
        macaddr: str
            The MAC address to find.  The format is "xx:xx:xx:xx:xx:xx".

        servers:
            Optional list of DHCP server names.  If not provided, then all
            avaialble DHCP servers will be checked.

        Returns
        -------
        The matching DHCP lease record if found, or None.
        """
        gen = self._fetch_dhcp_leases_tasker(servers=servers)
        tasks = await gen.__anext__()

        rec: dict
        async for rec in gen:
            if rec["mac"] == macaddr:
                found = rec
                break
        else:
            return None

        for t in tasks:
            t.cancel()

        found["dhcpServerName"] = self.dhcp_servers.inv[rec["dhcpServer"]]  # noqa
        return found

    async def find_dhcp_lease_matching(
        self, matcher: Callable[[Dict], bool], servers: Optional[Sequence[str]] = None
    ) -> Sequence[dict]:
        found_records = list()

        gen = self._fetch_dhcp_leases_tasker(servers=servers)

        # pull the tasks from the generator; not used in this method.
        _ = await gen.__anext__()

        async for rec in gen:
            if matcher(rec):
                found_records.append(rec)

        for found in found_records:
            found["dhcpServerName"] = self.dhcp_servers.inv[found["dhcpServer"]]  # noqa

        return found_records

    # -------------------------------------------------------------------------
    #                            PRIVATE METHODS
    # -------------------------------------------------------------------------

    async def _fetch_dhcp_leases_tasker(self, servers: Optional[Sequence[str]] = None):
        """
        This method generates DHCP lease records found on the DHCP servers.

        Parameters
        ----------
        servers:
            Optional list of DHCP server names.  If not provided, then all
            avaialble DHCP servers will be checked.

        Yields
        ------
        DHCP lease record (dict)
        """

        if not self.dhcp_servers:
            await self.fetch_dhcp_servers()

        servers_ip = (
            [self.dhcp_servers[s_] for s_ in servers]
            if servers
            else self.dhcp_servers.values()
        )

        tasks = [
            asyncio.ensure_future(
                self.get(
                    "/dhcpserver/dhcpActiveLeases", params=dict(serverIp=server_ip)
                )
            )
            for server_ip in servers_ip
        ]

        yield tasks

        for next_page in asyncio.as_completed(tasks):
            # TODO: due to an "issue" in TCPWave, some DHCP servers may not respond; therefore
            #       ignore ReadTimeout error until further updates.
            try:
                res: Response = await next_page
            except ReadTimeout:
                continue

            if res.is_error:
                if res.text.startswith("TIMS-3961"):
                    # this means the DHCP server could be offline; skipping.
                    continue

            res.raise_for_status()
            body = res.json()
            for rec in body["rows"]:
                yield rec
