# core/meta_data.py
import json
from urllib.parse import quote

from config.config import STREET_VIEW_CONFIG
from utils.http_client import http_client
from utils.logger import logger, log_exception


def get_panorama_id(bd_x, bd_y):
    """获取全景图ID

    Args:
        bd_x: 百度墨卡托x坐标
        bd_y: 百度墨卡托y坐标

    Returns:
        str: 全景图ID 或 None
    """
    if bd_x is None or bd_y is None:
        logger.warning("Cannot get panorama ID for None coordinates")
        return None

    # 请求接口1
    url = 'https://mapsv0.bdimg.com/'
    params = {
        'qt': 'qsdata',
        'x': bd_x,
        'y': bd_y,
        'mode': 'day',
        'type': 'street',
        'action': 0,
        'pc': 1
    }

    try:
        response = http_client.get_json(url, params)
        content = response.get('content', {})
        panorama_id = content.get('id')

        if not panorama_id:
            logger.warning(f"No panorama ID found for coordinates ({bd_x}, {bd_y})")
            return None

        logger.debug(f"Found panorama ID: {panorama_id}")
        return panorama_id
    except Exception as e:
        log_exception(e, f"Failed to get panorama ID for coordinates ({bd_x}, {bd_y})")
        return None


def get_panorama_metadata(panorama_id, target_year=None):
    """获取全景图元数据

    Args:
        panorama_id: 全景图ID
        target_year: 目标年份，如果指定则尝试获取该年份的全景图ID

    Returns:
        tuple: (新的全景图ID, 移动方向, 元数据内容) 或 (None, None, None)
    """
    if not panorama_id:
        return None, None, None

    # 请求接口2
    url = 'https://mapsv0.bdimg.com/'
    params = {
        'qt': 'sdata',
        'sid': panorama_id,
        'pc': 1
    }

    try:
        response = http_client.get_json(url, params)
        if not response or 'content' not in response or not response['content']:
            logger.warning(f"No content found in panorama metadata for ID {panorama_id}")
            return None, None, None

        content = response['content'][0]

        # 如果指定了目标年份，查找匹配的年份
        if target_year:
            timeline = content.get('TimeLine', [])
            matched_id = None

            for item in timeline:
                if item.get('Year') == str(target_year):
                    matched_id = item.get('ID')
                    logger.debug(f"Found matching year {target_year}, new ID: {matched_id}")

                    # 如果找到匹配的年份，递归获取该年份的元数据
                    if matched_id and matched_id != panorama_id:
                        return get_panorama_metadata(matched_id)
                    break

            if not matched_id:
                logger.warning(f"No panorama found for year {target_year}")
                return None, None, None

        # 提取移动方向
        move_dir = content.get('MoveDir')

        return panorama_id, move_dir, content
    except Exception as e:
        log_exception(e, f"Failed to get panorama metadata for ID {panorama_id}")
        return None, None, None