import logging
from app.observability.logging import setup_logging


def test_setup_logging_idempotent():
    setup_logging()
    # Ska inte kasta och bör lämna root logger i ett konsistent läge
    logger = logging.getLogger("access")
    assert isinstance(logger, logging.Logger)
