import certifi
import certifi_win32.wincerts
import wrapt

global certifi_where

try:

    # patch certifi.where so it uses the Windows cert store
    certifi_where = None

    def wrap_where(wrapped, instance, args, kwargs):
        import certifi_win32.wincerts
        return certifi_win32.wincerts.where()

    certifi_where = certifi.where
    certifi_win32.wincerts.CERTIFI_PEM = certifi.where()

    # Wrap the certify.where function
    wrapt.wrap_function_wrapper(certifi, 'where', wrap_where)

except Exception as e:
    print(str(e))
    raise

import requests
import requests.certs
