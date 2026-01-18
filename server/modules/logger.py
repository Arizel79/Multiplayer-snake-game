import os
import sys
from pathlib import Path
from loguru import logger


def setup_logging(console_level, log_file, file_level):
    print(console_level, log_file, file_level)
    logger.remove()

    logger.configure()

    def patcher(record):
        record["extra"]["rel_path"] = os.path.relpath(record["file"].path)

    patched_logger = logger.patch(patcher)

    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        " <cyan>{file}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{extra[rel_path]}:{line} | "
        "{message}"
    )

    patched_logger.add(
        sys.stderr,
        format=console_format,
        level=console_level,
        colorize=True,
    )

    if log_file is not None:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        patched_logger.add(
            log_file,
            format=file_format,
            level=file_level,
            rotation="100 MB",
        )

    return patched_logger



