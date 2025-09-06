import os
import structlog


def _get_logger():
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
    )
    return structlog.get_logger().bind(app="legal-simplifier", level=level)


logger = _get_logger()
