"""坐标转换模块

本模块提供了WGS84坐标系到百度墨卡托坐标系的转换功能。

注意:
    由于百度地图坐标转换API的配额限制，除非转换精度要求在1m以内，建议使用该方法进行转换。
    本模块主要用于与coordinate_api模块的精度比较基准。

优点:
    - 无需依赖百度地图API，不受限额限制
    - 适用于大批量坐标转换场景
    - 转换精度通常可满足一般应用需求
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.logger import logger, log_exception
from .CoordinatesConverterPro import wgs84tobd09ll, bd09lltobd09mc

def wgs2bd09mc(wgs_x, wgs_y):
    """将WGS84坐标转换为百度墨卡托坐标

    Args:
        wgs_x: WGS84经度
        wgs_y: WGS84纬度

    Returns:
        tuple: (百度墨卡托x坐标, 百度墨卡托y坐标) 或 (None, None)
    """
    try:
        # 先将WGS84转换为百度经纬度坐标
        bd_lon, bd_lat = wgs84tobd09ll(wgs_x, wgs_y)
        # 再将百度经纬度坐标转换为百度墨卡托坐标
        mc_x, mc_y = bd09lltobd09mc(bd_lon, bd_lat)
        return mc_x, mc_y
    except Exception as e:
        log_exception(e, "Failed to convert coordinates")
        return None, None

def batch_convert_coordinates(coordinate_pairs, max_workers=10):
    """批量转换坐标

    Args:
        coordinate_pairs: 包含(wgs_x, wgs_y)坐标对的列表
        max_workers: 最大并行工作线程数

    Returns:
        dict: 映射原始坐标对到转换后的坐标 {(wgs_x, wgs_y): (bd_x, bd_y)}
    """
    results = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_coords = {
            executor.submit(wgs2bd09mc, wgs_x, wgs_y): (wgs_x, wgs_y)
            for wgs_x, wgs_y in coordinate_pairs
        }

        # 收集结果
        for future in as_completed(future_to_coords):
            coords = future_to_coords[future]
            try:
                bd_x, bd_y = future.result()
                results[coords] = (bd_x, bd_y)
            except Exception as e:
                log_exception(e, f"Error processing coordinates {coords}")
                results[coords] = (None, None)

    return results