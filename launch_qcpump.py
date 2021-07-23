"""QCPump main entry point"""
import sys

if 'win' in  sys.platform.lower():
    import patch_certs
import qcpump

qcpump.main()
