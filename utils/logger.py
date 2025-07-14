# utils/logger.py
import logging
import sys
from datetime import datetime
from pathlib import Path

from config.config import LOG_DIR


def setup_logger(name='street_view_crawler', log_file=None):
    """设置日志记录器"""
    if log_file is None:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        log_file = LOG_DIR / f"{name}_{timestamp}.log"

    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # 创建文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    # 创建格式化器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # 添加处理器到记录器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


logger = setup_logger()


def log_exception(e, message="An error occurred"):
    """记录异常"""
    logger.error(f"{message}: {str(e)}", exc_info=True)