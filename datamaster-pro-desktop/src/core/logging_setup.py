import logging
import sys
from pathlib import Path

_LOG_CONFIGURED = False

def configure_logging(log_dir: str | Path, level: int = logging.INFO) -> None:
    global _LOG_CONFIGURED
    if _LOG_CONFIGURED:
        return

    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    file_path = log_path / "datamaster.log"

    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-7s %(name)-30s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(file_path, encoding="utf-8", mode="a")
    file_handler.setLevel(level)
    file_handler.setFormatter(fmt)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    _LOG_CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
