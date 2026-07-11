import logging

def setup_logger():
    logger = logging.getLogger("tmdb_etl")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formato = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # salida por consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formato)
    logger.addHandler(console_handler)

    # salida a archivo
    file_handler = logging.FileHandler("etl.log", encoding="utf-8")
    file_handler.setFormatter(formato)
    logger.addHandler(file_handler)

    return logger

logger = setup_logger()