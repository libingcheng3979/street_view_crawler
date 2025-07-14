"""
本模块用于对比coordinate_api模块与coordinate_math模块的转换结果。

注意:
    本模块与coordinate_api模块、coordinate_math模块均不参与项目的正式运行，只为评估二者转换结果的差异，实现坐标转换的核心模块是CoordinatesConverterPro与coordinate。
    *如果需要更加精准的坐标转换结果可以在配置文件中填入api key并修改coordinate中相关代码。
"""

import sys
from core import coordinate_api as real_coord
from core import coordinate_math as fake_coord
from utils.logger import logger


def compare_coordinates(test_points):
    """比较两种坐标转换方法的结果

    Args:
        test_points: List of (lon, lat) tuples to test
    """
    print("\n=== 坐标转换方法比较 ===")
    print("格式：WGS84坐标 -> [官方API结果, 本地转换结果, 差值]")
    print("-" * 80)

    for lon, lat in test_points:
        # 获取两种方法的转换结果
        real_x, real_y = real_coord.wgs2bd09mc(lon, lat)
        fake_x, fake_y = fake_coord.wgs2bd09mc(lon, lat)

        # 计算差值
        if real_x is not None and fake_x is not None:
            diff_x = abs(real_x - fake_x)
            diff_y = abs(real_y - fake_y)

            print(f"\nWGS84坐标: ({lon}, {lat})")
            print(f"X坐标比较:")
            print(f"  官方API: {real_x:.6f}")
            print(f"  本地转换: {fake_x:.6f}")
            print(f"  差值: {diff_x:.6f} 米")
            print(f"Y坐标比较:")
            print(f"  官方API: {real_y:.6f}")
            print(f"  本地转换: {fake_y:.6f}")
            print(f"  差值: {diff_y:.6f} 米")

            # 设置警告阈值（比如差值超过1米）
            threshold = 1.0
            if diff_x > threshold or diff_y > threshold:
                print("⚠️ 警告：坐标差值较大！")
        else:
            print(f"\nWGS84坐标: ({lon}, {lat})")
            print("转换失败：某个方法返回了None")


def main():
    # 测试点列表：可以根据需要添加更多测试点
    test_points = [
        # 北京天安门
        (116.397428, 39.90923),
        # 上海东方明珠
        (121.4952, 31.2424),
        # 广州塔
        (113.3172, 23.1192),
        # 深圳平安金融中心
        (114.0552, 22.5435),
        # 一个国外坐标（纽约时代广场）
        (-73.9855, 40.7580)
    ]

    try:
        compare_coordinates(test_points)
    except Exception as e:
        logger.error(f"比较过程中发生错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()