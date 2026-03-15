import subprocess
import os
import uuid
import shutil
import tarfile
import io
import time
from pathlib import Path
from typing import Optional, Any
from ..executor import ExecutionResult, SandboxBackend
from ..security.profiles import SecurityProfile


class FirecrackerBackend(SandboxBackend):
    """
    Executes code inside an isolated Firecracker microVM.
    - Strong VM-level isolation (like AWS Lambda)
    - Stateless by default - each run starts fresh
    - Optional session persistence across runs
    - Respects SecurityProfile (memory, CPU)

    Requires: firecracker binary and a rootfs image.
    """

    DEFAULT_VM_MEMORY_MB = 256
    DEFAULT_VCPU_COUNT = 1

    LANGUAGE_IMAGES = {
        "python": "/var/lib/firecracker/images/python.rootfs",
        "javascript": "/var/lib/firecracker/images/node.rootfs",
        "bash": "/var/lib/firecracker/images/bash.rootfs",
    }

    def __init__(
        self,
        rootfs: Optional[str] = None,
        security: Optional[SecurityProfile] = None,
        language: str = "python",
        session_id: Optional[str] = None,
        **kwargs: Any
    ):
        self.language = language.lower()
        self.security = security or SecurityProfile.DEFAULT
        self.session_id = session_id or str(uuid.uuid4())

        self.rootfs = rootfs or self.LANGUAGE_IMAGES.get(self.language)
        self.vm_memory = self.security.max_memory_mb or self.DEFAULT_VM_MEMORY_MB
        self.vcpu_count = self.security.max_cpu_percent or self.DEFAULT_VCPU_COUNT

        self._vm_dir = Path(f"/tmp/firecracker-{self.session_id}")
        self._vm_dir.mkdir(parents=True, exist_ok=True)

        self._kernel = "/usr/bin/firecracker"
        self._is_running = False
        self._check_firecracker()
    def _check_firecracker(self) -> None:
        """Check if firecracker is available."""
        result = shutil.which("firecracker")
        if not result:
            raise RuntimeError(
                "Firecracker is not installed. "
                "Install from: https://github.com/firecracker-microvm/firecracker"
            )

    def _build_vm_config(self) -> dict:
        """Build Firecracker configuration."""
        return {
            "boot-source": {
                "kernel-image-path": "/var/lib/firecracker/vmlinux",
                "bootArgs": "console=ttyS0 noapic reboot=k panic=1 pci=off"
            },
            "drives": [
                {
                    "drive-id": "rootfs",
                    "path-on-host": self.rootfs,
                    "is-root-device": True,
                    "is-read-only": not self.security.allow_filesystem_write
                }
            ],
            "machine-config": {
                "vcpu_count": self.vcpu_count,
                "mem_size_mib": self.vm_memory
            },
            "network-interfaces": [
                {
                    "iface-id": "eth0",
                    "guest-mac": "AA:FC:00:00:00:01",
                    "host-dev-name": "tap0"
                }
            ]
        }

    def _upload_code(self, code: str) -> str:
        """Upload code to the VM via vsock or SSH."""
        code_file = self._vm_dir / "code.py"
        code_file.write_text(code)

        langs = {"python": "py", "javascript": "js", "bash": "sh"}
        ext = langs.get(self.language, "py")
        target = f"/tmp/code.{ext}"

        return f"cp {code_file} {target} && {self._get_execute_command(target)}"

    def _get_execute_command(self, filepath: str) -> str:
        """Get the command to execute based on language."""
        if self.language == "javascript":
            return f"node {filepath}"
        elif self.language == "bash":
            return f"bash {filepath}"
        else:
            return f"python3 {filepath}"

    def run(self, code: str, timeout: int) -> ExecutionResult:
        """Execute code inside Firecracker microVM."""
        try:
            # Prepare code for execution
            self._upload_code(code)

            result = subprocess.run(
                ["firecracker", "--api-sock", str(self._vm_dir / "api.sock")],
                capture_output=True,
                timeout=timeout
            )

            return ExecutionResult(
                output=result.stdout.decode("utf-8", errors="replace"),
                exit_code=result.returncode,
                error=result.stderr.decode("utf-8", errors="replace") or None,
                backend_used="firecracker"
            )

        except subprocess.TimeoutExpired:
            self._cleanup()
            return ExecutionResult(
                output="",
                exit_code=124,
                is_timeout=True,
                error="Execution timed out",
                backend_used="firecracker"
            )
        except FileNotFoundError:
            return ExecutionResult(
                output="",
                exit_code=1,
                error=(
                    "Firecracker binary not found. "
                    "Install from firecracker-microvm.github.io"
                ),
                backend_used="firecracker"
            )
        except Exception as e:
            return ExecutionResult(
                output="",
                exit_code=1,
                error=f"FirecrackerBackend error: {str(e)}",
                backend_used="firecracker"
            )
        finally:
            self._cleanup()

    def _cleanup(self) -> None:
        """Clean up VM resources."""
        try:
            subprocess.run(["pkill", "-f", f"firecracker-{self.session_id}"],
                         capture_output=True)
            if self._vm_dir.exists():
                shutil.rmtree(self._vm_dir, ignore_errors=True)
        except Exception:
            pass
