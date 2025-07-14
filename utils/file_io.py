# utils/file_io.py
import csv
import os
import json
import pandas as pd
from pathlib import Path

from utils.logger import logger


def read_csv(file_path, encoding='utf-8'):
    """读取CSV文件"""
    try:
        df = pd.read_csv(file_path, encoding=encoding)
        logger.info(f"Successfully read CSV file: {file_path}, rows: {len(df)}")
        return df
    except Exception as e:
        logger.error(f"Failed to read CSV file {file_path}: {str(e)}")
        raise


def save_csv(df, file_path, encoding='utf-8-sig'):
    """保存DataFrame到CSV文件"""
    try:
        df.to_csv(file_path, index=False, encoding=encoding)
        logger.info(f"Successfully saved CSV file: {file_path}, rows: {len(df)}")
    except Exception as e:
        logger.error(f"Failed to save CSV file {file_path}: {str(e)}")
        raise


def save_to_file(content, file_path, mode='w', encoding='utf-8'):
    """保存内容到文件"""
    try:
        with open(file_path, mode, encoding=encoding) as f:
            f.write(content)
        logger.info(f"Successfully saved file: {file_path}")
    except Exception as e:
        logger.error(f"Failed to save file {file_path}: {str(e)}")
        raise


def load_progress(progress_file):
    """加载进度信息，用于断点续传"""
    if not os.path.exists(progress_file):
        return set()

    try:
        with open(progress_file, 'r') as f:
            return set(line.strip() for line in f)
    except Exception as e:
        logger.error(f"Failed to load progress file {progress_file}: {str(e)}")
        return set()


def save_progress(processed_ids, progress_file):
    """保存进度信息，用于断点续传"""
    try:
        with open(progress_file, 'w') as f:
            for pid in processed_ids:
                f.write(f"{pid}\n")
        logger.info(f"Successfully saved progress to {progress_file}")
    except Exception as e:
        logger.error(f"Failed to save progress to {progress_file}: {str(e)}")