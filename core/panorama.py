# core/panorama.py
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from config.config import STREET_VIEW_CONFIG, PANORAMIC_IMAGE_DIR
from utils.http_client import http_client
from utils.image_utils import save_image, stitch_tiles
from utils.logger import logger, log_exception


def calculate_tile_info(zoom_level):
    """根据缩放级别计算瓦片信息

    Args:
        zoom_level: 缩放级别(1-5)

    Returns:
        tuple: (行数, 列数)
    """
    if zoom_level == 1:
        return 1, 1
    elif zoom_level == 2:
        return 1, 2
    elif zoom_level == 3:
        return 2, 4
    elif zoom_level == 4:
        return 4, 8
    elif zoom_level == 5:
        return 8, 16
    else:
        logger.warning(f"Invalid zoom level: {zoom_level}, using default level 3")
        return 2, 4


def download_panorama_tile(panorama_id, row, col, zoom_level):
    """下载全景图瓦片

    Args:
        panorama_id: 全景图ID
        row: 行索引
        col: 列索引
        zoom_level: 缩放级别

    Returns:
        tuple: ((row, col), 瓦片数据) 或 ((row, col), None)
    """
    # 请求接口4
    url = 'https://mapsv0.bdimg.com/'
    params = {
        'qt': 'pdata',
        'sid': panorama_id,
        'pos': f"{row}_{col}",
        'z': zoom_level,
        'from': 'PC'
    }

    try:
        image_data = http_client.get_image(url, params)
        return (row, col), image_data
    except Exception as e:
        log_exception(e, f"Failed to download panorama tile ({row}, {col}) for ID {panorama_id}")
        return (row, col), None


def download_panorama(panorama_id, pid, lon, lat, zoom_level=3):
    """下载并拼接全景图

    Args:
        panorama_id: 全景图ID
        pid: 采样点ID
        lon: 经度
        lat: 纬度
        zoom_level: 缩放级别

    Returns:
        str: 保存的图片文件路径 或 None
    """
    if not panorama_id:
        logger.warning(f"Cannot download panorama for None panorama_id")
        return None

    # 创建保存图片的目录
    os.makedirs(PANORAMIC_IMAGE_DIR, exist_ok=True)

    # 计算瓦片行列数
    rows, cols = calculate_tile_info(zoom_level)

    # 下载所有瓦片
    tiles = {}
    futures = []

    with ThreadPoolExecutor(max_workers=rows * cols) as executor:
        # 提交下载任务
        for row in range(rows):
            for col in range(cols):
                future = executor.submit(
                    download_panorama_tile,
                    panorama_id,
                    row,
                    col,
                    zoom_level
                )
                futures.append(future)

        # 收集结果
        for future in as_completed(futures):
            try:
                position, tile_data = future.result()
                if tile_data:
                    tiles[position] = tile_data
            except Exception as e:
                log_exception(e, "Error processing panorama tile")

    # 检查是否所有瓦片都下载成功
    if len(tiles) != rows * cols:
        logger.warning(f"Not all tiles downloaded ({len(tiles)}/{rows * cols})")

    try:
        # 拼接瓦片
        if tiles:
            panorama = stitch_tiles(tiles, rows, cols)

            # 保存拼接后的全景图
            file_name = f"{pid}_{lon}_{lat}.jpg"
            file_path = PANORAMIC_IMAGE_DIR / file_name

            panorama.save(file_path, "JPEG", quality=95)
            logger.info(f"Saved panorama image: {file_name}")

            return str(file_path)
        else:
            logger.warning(f"No tiles downloaded for panorama ID {panorama_id}")
            return None
    except Exception as e:
        log_exception(e, f"Failed to stitch and save panorama for ID {panorama_id}")
        return None