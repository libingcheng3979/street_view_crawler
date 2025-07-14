# 街景爬虫项目

## 项目简介

本项目是一个基于百度地图API的街景爬虫工具，支持批量获取街景图片（四方向街景或全景图）。主要功能包括：

- **坐标转换**：无需API即可实现各坐标系之间的自由转换。
- **街景元数据获取**：通过道路采样点坐标获取街景元数据。
- **图片下载**：支持下载特定年份的四方向街景图或全景图。
  - *特定年份：支持自定义爬取年份，若不指定则默认爬取最新街景。*
  - *四方向街景图：支持按行驶方向确定四方向heading值或按绝对方向确定四方向heading值。*
  - *全景图：支持自定义缩放级别，缩放级别越高，瓦片越多，图片越清晰。*
- **断点续传**：中断后可继续爬取。
- **批量处理**：支持多线程批量处理采样点。
- **日志记录**：详细记录爬取过程，便于调试。

---

## 快速开始

### 1. 环境准备

确保安装 **Python 3.8+**，并安装项目依赖。
```bash
pip install -r requirements.txt
```
### 2. 准备输入数据

将采样点数据（CSV文件）放置到 `data/input/` 目录，文件需包含以下字段：

- **`PID`**：采样点ID
- **`Lon`**：经度
- **`Lat`**：纬度

具体可在`config/config.py` 中根据实际情况调整。

### 3. 运行爬虫

运行主程序启动爬虫。
```bash
python main.py
```
### 4. 查看结果

- **CSV结果**：爬取结果保存至 `data/output/csv/`，包含采样点ID、元数据和处理状态。由于元数据内容较长，因此不建议使用excel查看数据，可能会出现串行的情况。 
- **图片文件**：根据模式保存至以下目录：
  - 四方向街景图：`data/output/images/directional/`
  - 全景图：`data/output/images/panoramic/`
- **日志文件**：运行日志保存在 `data/output/logs/`。

---

## 项目结构

```plaintext
street_view_crawler/
├── config/                # 配置模块
├── core/                  # 核心功能模块
├── data/                  # 数据目录
│   ├── input/             # 输入文件
│   ├── output/            # 输出文件
├── utils/                 # 工具模块
├── main.py                # 主程序入口
├── requirements.txt       # 项目依赖
└── README.md              # 项目说明
```

## 注意事项
### 1. 百度地图API密钥
可在 `config/config.py` 中更新 `BAIDU_API_KEY` 为您的有效密钥。不追求坐标转换精度可不填入密钥。
### 2. 爬取延迟
默认设置了请求延迟以避免触发反爬机制，可在 `config/config.py` 中根据需求调整。
### 3. 断点续传
若爬取中断，可使用相关参数从上次中断处继续爬取。
```bash
python main.py --input sample.csv --output result.csv --mode directional --year 2021 --resume
```

## 参考资料
- https://github.com/whuyao/BaiduStreetViewSpider
- https://github.com/kingsley0107/streetview_images_crawler

## 声明
本爬虫代码仅供个人科研学习使用，请勿用于任何非科研和非法用途。

有任何疑问欢迎联系交流（libingcheng3979@163.com).