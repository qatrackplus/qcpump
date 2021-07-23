try:
    from qcpump.logs import get_logger
    import certifi_win32 # noqa: E402
    import certifi_win32.wincerts # noqa: E402
    certifi_win32.wincerts.generate_pem()
    import certifi
    logger = get_logger("certs")
    logger.debug(f"certifi-win32 PEM_PATH {certifi_win32.wincerts.where()}")
    logger.debug(f"certifi-win32 where {certifi_win32.wincerts.PEM_PATH}")
    logger.debug(f"certify.where() {certifi.where()}")
except Exception:
    logger.exception("Failed to patch certificates")
import requests  # noqa: E402
import requests.certs  # noqa: E402, F401
