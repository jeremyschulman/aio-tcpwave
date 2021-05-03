# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from typing import Optional
from os import getenv

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

from httpx import AsyncClient  # from httpx import  Response

# from tenacity import retry, wait_exponential

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["TCPWaveClient"]


# -----------------------------------------------------------------------------
#
#                                 CODE BEGINS
#
# -----------------------------------------------------------------------------


class TCPWaveClient(AsyncClient):
    """
    Base client class for Extreme TCPWave API access.  The following
    environment variables can be used:

    TCPWAVE_ADDR - str
        The URL to the TCPWave server inlcuding the "/tims/" endpoint

    TCPWAVE_SSL_CERT - str
        The path to the client SSL certificate file

    TCPWAVE_SSL_KEY - str
        The path to the client SSL certificate key file

    TCPWAVE_TOKEN - str
        The preconfigured API token bound to the IP address of the system using
        it (per TCPWave).

    TCPWAVE_ORG - str
        The default organizational value to used by APIs that require one.
    """

    DEFAULT_PAGE_SZ = 100
    DEFAULT_TIMEOUT = 30

    def __init__(
        self,
        tcpwave_token: Optional[str] = None,
        tcpwave_org: Optional[str] = None,
        **kwargs,
    ):
        kwargs.setdefault("timeout", self.DEFAULT_TIMEOUT)
        kwargs.setdefault("verify", False)

        # make `base_url` a requirement

        kwargs.setdefault("base_url", getenv("TCPWAVE_ADDR"))
        if not kwargs["base_url"]:
            raise RuntimeError("Missing required base_url")

        kwargs["base_url"] += "/rest/"

        # (User) client certificate files, if provided

        if "cert" not in kwargs:
            ssl_cert, ssl_key = getenv("TCPWAVE_SSL_CERT"), getenv("TCPWAVE_SSL_KEY")
            if ssl_cert and ssl_key:
                kwargs["cert"] = (ssl_cert, ssl_key)

        super(TCPWaveClient, self).__init__(**kwargs)

        if tcpwave_token or (tcpwave_token := getenv("TCPWAVE_TOKEN")):
            self.headers["TIMS-Session-Token"] = tcpwave_token

        self.tcpwave_org = tcpwave_org or getenv("TCPWAVE_ORG")

    @staticmethod
    def simple_api(meth):
        async def wrapper(*vargs, **kwargs):
            res = await meth(*vargs, **kwargs)
            res.raise_for_status()
            return res.json()

        return wrapper

    # -----------------------------------------------------------------------------
    #                            AsyncClient Overrides
    # -----------------------------------------------------------------------------

    # async def request(self, *vargs, **kwargs) -> Response:
    #     @retry(wait=wait_exponential(multiplier=1, min=4, max=10))
    #     async def _do_rqst():
    #         res = await super(XiqBaseClient, self).request(*vargs, **kwargs)
    #         if res.status_code == 400 and 'UNKNOWN' in res.text:
    #             print("XIQ client request: retry")
    #             res.raise_for_status()
    #         return res
    #
    #     return await _do_rqst()
