"""This file will patch requests/certifi so that requests will use a
combination of the certificates included with the python-certifi package, as
well as the Windows certificate store.  See
https://pypi.org/project/python-certifi-win32/

This is necessary in some environments where there may be proxies or other
network related software that cause SSL verification to fail for <reasons>.

It should be imported before requests/certifi are imported (many
packages import requests so it's a good idea to have it imported as the
first thing that ever gets imported when launching your program.

I had issues getting the python-certifi-win32 to work in all use cases (e.g.
running as an admin or non-admin user) which is why there is some extra
patching of file locations (`where`) going on below here.

(Fair warning: The steps below are based on a fair amount of trial and error
and pulling of hair and modifying it may cause things to stop working)

"""

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
else:
    logger.debug(f"certifi-win32 PEM_PATH {certifi_win32.wincerts.where()}")
    logger.debug(f"certifi-win32 where {certifi_win32.wincerts.PEM_PATH}")
    logger.debug(f"certify.where() {certifi.where()}")
