import loguru
import os

LOGS_PATH = "logs"

logger: loguru.logger

def init_log(logs_path=LOGS_PATH):
    logger = loguru.logger
    os.makedirs(logs_path, exist_ok=True)
    logger.add(
        f"{LOGS_PATH}/info.log",
        rotation="1 day",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        encoding="utf-8",
    )
    logger.add(
        f"{LOGS_PATH}/error.log",
        rotation="1 day",
        retention="7 days",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        encoding="utf-8",
    )

    logger.info("log init success")
    return logger

logger = init_log()