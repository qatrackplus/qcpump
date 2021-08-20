"""QCPump main entry point"""

from pathlib import Path
from qcpump.settings import get_config_dir

nopatch = Path(get_config_dir()) / "nopatch.txt"

if not nopatch.exists():
    try:
        import patch_certs  # noqa: F401
    except Exception:
        pass

import qcpump

qcpump.main()
