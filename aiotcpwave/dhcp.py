# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from typing import Optional, Sequence, Dict
import asyncio
import re

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

from httpx import Response, ReadTimeout

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from .client import TCPWaveClient


class TCPWaveDCHP(TCPWaveClient):
    """
    This TCPWave client mixin provides DCHP related features.

    The caller needs to invoke the `fetch_dhcp_servers` method before calling
    any of other DHCP "find" methods.
    """

    def __init__(self, *vargs, **kwargs):
        super(TCPWaveDCHP, self).__init__()
        self.dhcp_servers: Optional[Dict[str]] = dict()

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
        List of DHCP server records.
        """
        res = await self.get(
            "/dhcpserver/list", params=params or dict(orgName=self.tcpwave_org)
        )
        res.raise_for_status()
        body = res.json()
        self.dhcp_servers = {rec["name"]: rec["v4_ipaddress"] for rec in body}
        return body

    async def fetch_dhcp_leases(self, servers: Optional[Sequence[str]] = None):
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

        servers_ip = (
            [self.dhcp_servers[s_] for s_ in servers]
            if servers
            else self.dhcp_servers.values()
        )

        for next_page in asyncio.as_completed(
            [
                self.get(
                    "/dhcpserver/dhcpActiveLeases", params=dict(serverIp=server_ip)
                )
                for server_ip in servers_ip
            ]
        ):
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
        async for rec in self.fetch_dhcp_leases(servers=servers):
            if rec["address"] == ipaddr:
                return rec

        return None

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
        async for rec in self.fetch_dhcp_leases(servers=servers):
            if rec["mac"] == macaddr:
                return rec

        return None

    async def find_dhcp_lease_name(
        self,
        name: Optional[str] = None,
        name_regx: Optional[str] = None,
        servers: Optional[Sequence[str]] = None,
    ) -> Sequence[dict]:
        """
        This coroutine will find all DHCP lease records whose "name" field matches
        the provided value.

        If `name_regx` is provide then the matching is done using a case-insensitive
        regular expression match using this value.

        If `name` is provided, then matching is found within the record; using
        a case-ignore match.  For exmaple: if `name` is "Jeremy" a match would
        be found for a DHCP lease with name of "JEREMY-LAPTOP"

        Parameters
        ----------
        name: str
            Name match

        name_regx: str
            Name match using regular expression

        servers:
            Optional list of DHCP server names.  If not provided, then all
            avaialble DHCP servers will be checked.

        Returns
        -------
        List of matching DHCP lease records, or empty-list if none found.
        """

        if name_regx:
            matcher_re = re.compile(name, re.IGNORECASE).search

            def matcher(_rec):
                matcher_re(string=_rec["name"])

        # find the `name` value in the DHCP lease record; case-ignore
        elif name:
            name = name.lower()

            def matcher(_rec):
                return False if not _rec["name"] else name in _rec["name"].lower()

        else:
            raise RuntimeError("name or name_regx required")

        found_records = list()

        async for rec in self.fetch_dhcp_leases(servers=servers):
            if matcher(rec):
                found_records.append(rec)

        return found_records
