import logging


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] -- %(levelname)s -- %(module)s: %(message)s'
    )
