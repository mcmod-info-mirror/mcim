
import os
import sys
import logging
from types import FrameType
from typing import cast
from loguru import logger
import time

from app.config import MCIMConfig

if os.getenv("TZ") is not None:
    time.tzset()

mcim_config = MCIMConfig.load()

LOG_PATH = mcim_config.log_path
if mcim_config.log_to_file:
    os.makedirs(LOG_PATH, exist_ok=True)

ENABLED: bool = False

EXCLUDED_ENDPOINTS = ["/metrics"]

class EndpointFilter(logging.Filter):
    """Filter class to exclude specific endpoints from log entries."""

    def __init__(self, excluded_endpoints: list[str]) -> None:
        """
        Initialize the EndpointFilter class.

        Args:
            excluded_endpoints: A list of endpoints to be excluded from log entries.
        """
        self.excluded_endpoints = excluded_endpoints

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter out log entries for excluded endpoints.

        Args:
            record: The log record to be filtered.

        Returns:
            bool: True if the log entry should be included, False otherwise.
        """
        return record.args and len(record.args) >= 3 and record.args[2] not in self.excluded_endpoints


class Logger:
    """输出日志到文件和控制台"""

    def __init__(self):
        # 文件的命名
        log_path = os.path.join(LOG_PATH, "fastapi", "{time:YYYY-MM-DD}.log")
        self.logger = logger
        # 清空所有设置
        self.logger.remove()
        # 判断日志文件夹是否存在，不存则创建
        if not os.path.exists(LOG_PATH):
            os.makedirs(LOG_PATH)
        # 添加控制台输出的格式,sys.stdout为输出到屏幕;关于这些配置还需要自定义请移步官网查看相关参数说明
        self.logger.add(
            sys.stdout,
            format="<green>{time:YYYYMMDD HH:mm:ss}</green> | "  # 颜色>时间
            #    "{process.name} | "  # 进程名
            #    "{thread.name} | "  # 进程名
            "<cyan>{module}</cyan>.<cyan>{function}</cyan> | "  # 模块名.方法名
            #    ":<cyan>{line}</cyan> | "  # 行号
            "<level>{level}</level>: "  # 等级
            "<level>{message}</level>",  # 日志内容
            level="INFO" if not mcim_config.debug else "DEBUG",
            backtrace=False,
            diagnose=False,
            filter=EndpointFilter(EXCLUDED_ENDPOINTS),
        )
        if mcim_config.log_to_file:
            # 日志写入文件
            self.logger.add(
                log_path,  # 写入目录指定文件
                format="{time:YYYYMMDD HH:mm:ss} - "  # 时间
                #    "{process.name} | "  # 进程名
                #    "{thread.name} | "  # 进程名
                "{module}.{function}:{line} - {level} -{message}",  # 模块名.方法名:行号
                encoding="utf-8",
                retention="7 days",  # 设置历史保留时长
                backtrace=True,  # 回溯
                diagnose=True,  # 诊断
                enqueue=True,  # 异步写入
                rotation="00:00",  # 每日更新时间
                # rotation="5kb",  # 切割，设置文件大小，rotation="12:00"，rotation="1 week"
                # filter="my_module"  # 过滤模块
                # compression="zip"   # 文件压缩
                level="INFO" if not mcim_config.debug else "DEBUG",
                filter=EndpointFilter(EXCLUDED_ENDPOINTS),
            )

    def get_logger(self):
        return self.logger

    def init_config(self):
        global ENABLED
        if not ENABLED:
            LOGGER_NAMES = ("uvicorn.asgi", "uvicorn.access", "uvicorn")

            # change handler for default uvicorn logger
            logging.getLogger().handlers = [InterceptHandler()]
            for logger_name in LOGGER_NAMES:
                logging_logger = logging.getLogger(logger_name)
                # log level
                if not mcim_config.debug:
                    logging_logger.setLevel(logging.INFO)
                else:
                    logging_logger.setLevel(logging.DEBUG)
                logging_logger.handlers = [InterceptHandler()]
            ENABLED = True


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:  # noqa: WPS609
            frame = cast(FrameType, frame.f_back)
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level,
            record.getMessage(),
        )

Loggers = Logger()
Loggers.init_config()
log = Loggers.get_logger()