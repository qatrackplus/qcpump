import os
import sys

import certifi_win32.wincerts
import wrapt

from qcpump.logs import get_logger
from qcpump.settings import frozen, root

global certifi_where


logger = get_logger("certs")


def wrap_certifi_pem():
    """Adapted from certifi_win32.wincerts"""
    logger.debug(f"CERTIFI_PEM pre patch {certifi_win32.wincerts.CERTIFI_PEM}")
    if not certifi_win32.wincerts.CERTIFI_PEM or not os.path.exists(certifi_win32.wincerts.CERTIFI_PEM):
        import certifi
        certifi_win32.wincerts.CERTIFI_PEM = os.path.join(root, "certifi", "cacert.pem")
        logger.debug(f"CERTIFI_PEM post patch {certifi_win32.wincerts.CERTIFI_PEM}")
        if not os.path.exists(certifi_win32.wincerts.CERTIFI_PEM):
            raise ValueError("Cannot find certifi cacert.pem")
    logger.debug(f"using CERTIFI_PEM {certifi_win32.wincerts.CERTIFI_PEM}")
    return certifi_win32.wincerts.CERTIFI_PEM


logger.debug(f"Frozen: {frozen} Windows: {'win' in sys.platform.lower()}")
if frozen and 'win' in sys.platform.lower():
    certifi_win32.wincerts.certifi_pem = wrap_certifi_pem
    wrap_certifi_pem()

try:

    # patch certifi.where so it uses the Windows cert store
    certifi_where = None

    def wrap_where(wrapped, instance, args, kwargs):
        import certifi_win32.wincerts
        return certifi_win32.wincerts.where()

    import certifi
    certifi_where = certifi.where
    certifi_win32.wincerts.CERTIFI_PEM = certifi.where()

    # Wrap the certify.where function
    wrapt.wrap_function_wrapper(certifi, 'where', wrap_where)

except Exception as e:
    print(str(e))
    raise

import requests  # noqa: E402
import requests.certs  # noqa: E402, F401
