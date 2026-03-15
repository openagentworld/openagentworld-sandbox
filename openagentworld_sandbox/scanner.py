import re


from .exceptions import ScanError


DANGEROUS_PATTERNS = [
    # Infinite loops
    (r"while\s+True", "Infinite loop 'while True' detected"),
    (r"while\s+1\b", "Infinite loop 'while 1' detected"),
    
    # Process forking/execution
    (r"fork\s*\(", "Fork bomb detected"),
    (r"os\.system\s*\(", "Dangerous 'os.system' call detected"),
    (r"subprocess\.call\s*\(", "Dangerous 'subprocess.call' detected"),
    (r"subprocess\.run\s*\(", "Dangerous 'subprocess.run' detected"),
    (r"subprocess\.Popen\s*\(", "Dangerous 'subprocess.Popen' detected"),
    (r"os\.popen\s*\(", "Dangerous 'os.popen' detected"),
    (r"spawn\s*\(", "Process spawn detected"),
    (r"execv\s*\(", "Dangerous 'execv' detected"),
    (r"execve\s*\(", "Dangerous 'execve' detected"),
    
    # Code execution
    (r"\beval\s*\(", "Dangerous 'eval' detected"),
    (r"\bexec\s*\(", "Dangerous 'exec' detected"),
    (r"compile\s*\(", "Dynamic code compilation detected"),
    (r"__import__\s*\(", "Dynamic import detected"),
    (r"importlib\.import_module\s*\(", "Dynamic module import detected"),
    
    # Threading/multiprocessing
    (r"import\s+threading", "Threading import detected"),
    (r"import\s+multiprocessing", "Multiprocessing import detected"),
    (r"import\s+concurrent", "Concurrent futures import detected"),
    (r"import\s+asyncio", "Asyncio import detected"),
    
    # File operations
    (r"open\s*\([^)]*,\s*['\"]w", "File write operation detected"),
    (r"open\s*\([^)]*,\s*['\"]a", "File append operation detected"),
    (r"chmod\s*\(", "File permission change detected"),
    (r"chown\s*\(", "File ownership change detected"),
    (r"\bremove\s*\(", "File deletion detected"),
    (r"\bunlink\s*\(", "File deletion detected"),
    (r"\brename\s*\(", "File rename detected"),
    (r"\bmkdir\s*\(", "Directory creation detected"),
    (r"\brmdir\s*\(", "Directory removal detected"),
    (r"shutil\.rmtree\s*\(", "Recursive directory deletion detected"),
    (r"shutil\.move\s*\(", "File move detected"),
    (r"shutil\.copy\s*\(", "File copy detected"),
    
    # Network/sockets
    (r"socket\.socket\s*\(", "Socket creation detected"),
    (r"urllib\.request", "URL request library detected"),
    (r"urllib2", "URL request library detected"),
    (r"import\s+requests", "Requests library detected"),
    (r"import\s+telnetlib", "Telnet library detected"),
    (r"import\s+ftplib", "FTP library detected"),
    (r"import\s+smtplib", "SMTP library detected"),
    (r"import\s+imaplib", "IMAP library detected"),
    (r"import\s+poplib", "POP3 library detected"),
    
    # Serialization dangers
    (r"pickle\.load", "Pickle deserialization detected"),
    (r"yaml\.unsafe", "Unsafe YAML loading detected"),
    (r"yaml\.load\s*\([^,)]*\)\s*(?!Loader)", "Unsafe YAML loading detected"),
    (r"marshal\.load", "Marshal deserialization detected"),
    (r"import\s+shelve", "Shelve module detected"),
    
    # Process control
    (r"os\.kill\s*\(", "Process kill detected"),
    (r"os\.killpg\s*\(", "Process group kill detected"),
    (r"signal\.signal\s*\(", "Signal handler registration detected"),
    
    # Memory/resource exhaustion
    (r"\[\s*\w+\s*\]\s*\*\s*\d{5,}", "Large list allocation detected"),
    (r"\(\s*\)\s*\*\s*\d{5,}", "Large tuple allocation detected"),
    
    # Input capture
    (r"\binput\s*\(\s*['\"]", "Input prompt detected"),
    
    # CTypes
    (r"import\s+ctypes", "C types import detected"),
    
    # Misc dangerous
    (r"sys\.settrace\s*\(", "Debugger/tracer detected"),
    (r"sys\.setprofile\s*\(", "Profiler detected"),
]


def scan(code: str) -> None:
    """
    Static analysis to detect dangerous patterns before execution.
    
    Args:
        code: The code to scan
        
    Raises:
        ScanError: If dangerous pattern is detected
    """
    for pattern, message in DANGEROUS_PATTERNS:
        if re.search(pattern, code, re.IGNORECASE):
            raise ScanError(f"Pre-execution scanner blocked: {message}")
