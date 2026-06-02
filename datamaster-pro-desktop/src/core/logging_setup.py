import logging
import logging.config
import sys
from pathlib import Path

import yaml

_LOG_CONFIGURED = False


def configure_logging(log_dir: str | Path, level: int = logging.INFO) -> None:
    global _LOG_CONFIGURED
    if _LOG_CONFIGURED:
        return

    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    yaml_path = Path(__file__).parent.parent.parent / "logging.yaml"

    if yaml_path.exists():
        with open(yaml_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        config["handlers"]["file"]["filename"] = str(log_path / "datamaster.log")
        config["handlers"]["sync_file"]["filename"] = str(log_path / "sync.log")

        if "audit_file" in config.get("handlers", {}):
            config["handlers"]["audit_file"]["filename"] = str(log_path / "audit.log")

        logging.config.dictConfig(config)
    else:
        _configure_fallback(log_path, level)

    from src.core.session_context import SessionFilter
    session_filter = SessionFilter()

    root = logging.getLogger()
    for handler in root.handlers:
        handler.addFilter(session_filter)

    audit_logger = logging.getLogger("audit")
    audit_logger.setLevel(logging.INFO)
    audit_logger.propagate = False
    audit_logger.addFilter(session_filter)

    if not audit_logger.handlers:
        from logging.handlers import RotatingFileHandler
        audit_handler = RotatingFileHandler(
            log_path / "audit.log",
            encoding="utf-8",
            maxBytes=5_242_880,
            backupCount=3,
        )
        audit_fmt = logging.Formatter(
            "%(asctime)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        audit_handler.setFormatter(audit_fmt)
        audit_logger.addHandler(audit_handler)

    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        import traceback
        tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        if root.isEnabledFor(logging.ERROR):
            root.error("Uncaught Exception - Application Crash\n%s", tb_text)

    sys.excepthook = handle_exception
    _LOG_CONFIGURED = True


def _configure_fallback(log_path: Path, level: int):
    import logging.handlers
    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-7s %(name)-30s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = logging.handlers.RotatingFileHandler(
        log_path / "datamaster.log",
        encoding="utf-8",
        maxBytes=10_485_760,
        backupCount=5,
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(fmt)
    root = logging.getLogger()
    if root.hasHandlers():
        root.handlers.clear()
    root.setLevel(logging.DEBUG)
    root.addHandler(file_handler)
    root.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
