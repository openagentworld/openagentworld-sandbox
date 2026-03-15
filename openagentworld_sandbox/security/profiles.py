from dataclasses import dataclass, field
from typing import List, Optional, ClassVar


@dataclass
class SecurityProfile:
    """
    Preset security configurations for code execution.

    Usage:
        executor = SafeExecutor(backend="docker", security=SecurityProfile.STRICT)
    """
    blocked_imports: List[str] = field(default_factory=list)
    network_access: bool = True
    max_memory_mb: Optional[int] = None
    max_cpu_percent: Optional[int] = None
    wipe_on_exit: bool = False
    allow_filesystem_write: bool = True

    # --- Presets (assigned after class) ---
    DEFAULT: ClassVar["SecurityProfile"]
    STRICT: ClassVar["SecurityProfile"]
    PERMISSIVE: ClassVar["SecurityProfile"]


# --- Presets initialization ---

SecurityProfile.DEFAULT = SecurityProfile()

SecurityProfile.STRICT = SecurityProfile(
    blocked_imports=[
        "os", "sys", "subprocess", "socket",
        "shutil", "pathlib", "ctypes", "multiprocessing",
        "importlib", "pickle", "shelve"
    ],
    network_access=False,
    max_memory_mb=128,
    max_cpu_percent=50,
    wipe_on_exit=True,
    allow_filesystem_write=False
)

SecurityProfile.PERMISSIVE = SecurityProfile(
    network_access=True,
    allow_filesystem_write=True
)
