# config/config.py
import os
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent

# 数据目录
DATA_DIR = ROOT_DIR / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
CSV_OUTPUT_DIR = OUTPUT_DIR / "csv"
IMAGE_OUTPUT_DIR = OUTPUT_DIR / "images"
DIRECTIONAL_IMAGE_DIR = IMAGE_OUTPUT_DIR / "directional"
PANORAMIC_IMAGE_DIR = IMAGE_OUTPUT_DIR / "panoramic"
LOG_DIR = OUTPUT_DIR / "logs"
TEMP_DIR = DATA_DIR / "temp"

# 创建必要的目录
for directory in [INPUT_DIR, CSV_OUTPUT_DIR, DIRECTIONAL_IMAGE_DIR,
                  PANORAMIC_IMAGE_DIR, LOG_DIR, TEMP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# 文件配置
INPUT_CSV_FILE = "采样点.csv"  # 输入文件名
OUTPUT_CSV_FILE = "爬取结果.csv"       # 输出文件名

# CSV字段配置
LON_FIELD = 'Lon'          # 经度字段
LAT_FIELD = 'Lat'          # 纬度字段
PID_FIELD = 'PID'          # 采样点ID字段

# 百度地图API配置
BAIDU_API_KEY = ''  # 百度地图API密钥

# 街景图请求配置
STREET_VIEW_CONFIG = {
    'year': None,          # 指定年份，None表示使用最新数据
    'use_directional': False,  # True: 使用接口3爬取四方向街景，False: 使用接口4爬取全景图
    'use_move_dir': True,  # True: 根据行驶方向确定heading, False: 使用绝对数值确定heading
    'fovy': 90,            # 视场角
    'quality': 100,        # 图像质量
    'pitch': 0,            # 俯仰角
    'width': 500,          # 图像宽度
    'height': 500,         # 图像高度
    'panorama_zoom': 3     # 全景图缩放级别(1-5)
}

# HTTP请求配置
HTTP_CONFIG = {
    'max_retries': 3,       # 最大重试次数
    'retry_delay': 2,       # 重试延迟(秒)
    'timeout': 30,          # 请求超时时间(秒)
    'headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
        'Referer': 'https://map.baidu.com/',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
    }
}

# 爬取批次配置
BATCH_SIZE = 50             # 每批处理的采样点数量
BATCH_DELAY = 5             # 批次之间的延迟(秒)