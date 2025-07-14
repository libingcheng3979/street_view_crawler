# utils/image_utils.py
import os
import io
import numpy as np
from PIL import Image
from pathlib import Path

from utils.logger import logger, log_exception


def save_image(image_data, file_path):
    """保存图片数据到文件"""
    try:
        with open(file_path, 'wb') as f:
            f.write(image_data)
        logger.debug(f"Successfully saved image to {file_path}")
        return True
    except Exception as e:
        log_exception(e, f"Failed to save image to {file_path}")
        return False


def stitch_tiles(tiles, rows, cols):
    """拼接图像瓦片

    Args:
        tiles: 包含图像数据的二维数组
        rows: 行数
        cols: 列数

    Returns:
        拼接好的图像
    """
    try:
        # 把所有tiles转换为PIL图像
        pil_tiles = []
        for i in range(rows):
            row_tiles = []
            for j in range(cols):
                if (i, j) in tiles:
                    img = Image.open(io.BytesIO(tiles[(i, j)]))
                    row_tiles.append(img)
                else:
                    # 如果缺失瓦片，创建一个空白图像
                    logger.warning(f"Missing tile at position ({i}, {j})")
                    # 获取其他瓦片的大小
                    example_tile = next(iter(tiles.values()))
                    example_img = Image.open(io.BytesIO(example_tile))
                    blank_img = Image.new('RGB', example_img.size, (255, 255, 255))
                    row_tiles.append(blank_img)
            pil_tiles.append(row_tiles)

        # 获取单个瓦片的宽度和高度
        tile_width = pil_tiles[0][0].width
        tile_height = pil_tiles[0][0].height

        # 创建最终图像
        stitched = Image.new('RGB', (cols * tile_width, rows * tile_height))

        # 将瓦片放入最终图像
        for i in range(rows):
            for j in range(cols):
                stitched.paste(pil_tiles[i][j], (j * tile_width, i * tile_height))

        return stitched
    except Exception as e:
        log_exception(e, "Failed to stitch tiles")
        raise