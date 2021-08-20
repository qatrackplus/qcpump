"""QCPump main entry point"""
try:
    import patch_certs  # noqa: F401
except Exception:
    pass
import qcpump

qcpump.main()
