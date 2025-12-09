import logging

logging.basicConfig(
    filename="error.log",
    format="%(levelname)s %(asctime)s - %(message)s",
    level=logging.ERROR,
)

logger = logging.getLogger()
