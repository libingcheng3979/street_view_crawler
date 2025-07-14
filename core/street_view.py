# core/street_view.py
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from config.config import STREET_VIEW_CONFIG, DIRECTIONAL_IMAGE_DIR
from utils.http_client import http_client
from utils.image_utils import save_image
from utils.logger import logger, log_exception


def calculate_headings(move_dir, use_move_dir=True):
    """计算四个方向的heading值

    Args:
        move_dir: 移动方向
        use_move_dir: 是否根据移动方向计算heading

    Returns:
        list: 四个方向的heading值
    """
    if not use_move_dir:
        # 使用绝对数值
        return [0, 90, 180, 270]

    if move_dir is None:
        logger.warning("MoveDir is None, using absolute headings")
        return [0, 90, 180, 270]

    move_dir = float(move_dir)

    # 根据移动方向计算四个方向的heading
    if 0 <= move_dir < 90:
        return [move_dir, move_dir + 90, move_dir + 180, move_dir + 270]
    elif 90 <= move_dir < 180:
        return [move_dir - 90, move_dir, move_dir + 90, move_dir + 180]
    elif 180 <= move_dir < 270:
        return [move_dir - 180, move_dir - 90, move_dir, move_dir + 90]
    else:  # 270 <= move_dir < 360
        return [move_dir - 270, move_dir - 180, move_dir - 90, move_dir]


def download_street_view_image(panorama_id, heading, pitch=0, fovy=90, quality=100, width=500, height=500):
    """下载街景图片

    Args:
        panorama_id: 全景图ID
        heading: 相机朝向
        pitch: 俯仰角
        fovy: 视场角
        quality: 图像质量
        width: 图像宽度
        height: 图像高度

    Returns:
        bytes: 图片数据 或 None
    """
    # 请求接口3
    url = 'https://mapsv0.bdimg.com/'
    params = {
        'qt': 'pr3d',
        'fovy': fovy,
        'quality': quality,
        'panoid': panorama_id,
        'heading': heading,
        'pitch': pitch,
        'width': width,
        'height': height,
        'from': 'PC'
    }

    try:
        image_data = http_client.get_image(url, params)
        return image_data
    except Exception as e:
        log_exception(e, f"Failed to download street view image for ID {panorama_id}, heading {heading}")
        return None


def download_directional_images(panorama_id, move_dir, pid, lon, lat, use_move_dir=True):
    """下载四个方向的街景图片

    Args:
        panorama_id: 全景图ID
        move_dir: 移动方向
        pid: 采样点ID
        lon: 经度
        lat: 纬度
        use_move_dir: 是否根据移动方向计算heading

    Returns:
        list: 成功下载的图片文件路径
    """
    if not panorama_id:
        logger.warning(f"Cannot download images for None panorama_id")
        return []

    # 计算四个方向的heading
    headings = calculate_headings(move_dir, use_move_dir)

    # 创建保存图片的目录
    os.makedirs(DIRECTIONAL_IMAGE_DIR, exist_ok=True)

    downloaded_files = []
    futures = []

    with ThreadPoolExecutor(max_workers=4) as executor:
        # 提交下载任务
        for heading in headings:
            future = executor.submit(
                download_street_view_image,
                panorama_id,
                heading,
                STREET_VIEW_CONFIG['pitch'],
                STREET_VIEW_CONFIG['fovy'],
                STREET_VIEW_CONFIG['quality'],
                STREET_VIEW_CONFIG['width'],
                STREET_VIEW_CONFIG['height']
            )
            futures.append((future, heading))

        # 处理结果
        for future, heading in futures:
            try:
                image_data = future.result()
                if image_data:
                    file_name = f"{pid}_{heading:.1f}_{lon}_{lat}.jpg"
                    file_path = DIRECTIONAL_IMAGE_DIR / file_name

                    if save_image(image_data, file_path):
                        downloaded_files.append(str(file_path))
                        logger.info(f"Downloaded street view image: {file_name}")
                    else:
                        logger.warning(f"Failed to save street view image: {file_name}")
            except Exception as e:
                log_exception(e, f"Error processing image for heading {heading}")

    return downloaded_files