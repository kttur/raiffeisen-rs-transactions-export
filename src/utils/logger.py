import logging


def get_logger(name, level):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.hasHandlers():
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger
