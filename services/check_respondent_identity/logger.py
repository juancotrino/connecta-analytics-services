import logging


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] -- %(levelname)s -- %(module)s: %(message)s'
    )

def get_logger(name: str):
    return logging.getLogger(name)
