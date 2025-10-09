from typing import Callable

# Nivel puede ser: "info", "success", "warning", "error", "code"
LogFn = Callable[[str, str], None]

def noop_logger(level: str, msg: str) -> None:
    """Logger por defecto (no hace nada)."""
    return