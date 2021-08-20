import traceback

global certifi_where

try:
    import certifi
    import certifi_win32.wincerts  # noqa: E402
    import wrapt
    certifi_win32.wincerts.generate_pem()

    certifi_where = None

    def wrap_where(wrapped, instance, args, kwargs):
        import certifi_win32.wincerts
        return certifi_win32.wincerts.where()

    certifi_where = certifi.where
    certifi_win32.wincerts.CERTIFI_PEM = certifi.where()

    # Wrap the certify.where function
    wrapt.wrap_function_wrapper(certifi, 'where', wrap_where)
    exception = None

except Exception:
    exception = traceback.format_exc()

import requests  # noqa: E402
import requests.certs  # noqa: E402, F401
from qcpump.logs import get_logger  # noqa: E402
logger = get_logger("certs")
if exception:
    logger.error("Failed to patch certficates: %s" % exception)
logger.debug(f"certifi-win32 PEM_PATH {certifi_win32.wincerts.where()}")
logger.debug(f"certifi-win32 where {certifi_win32.wincerts.PEM_PATH}")
logger.debug(f"certify.where() {certifi.where()}")
