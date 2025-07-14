# main.py
import os
import sys
import time
import argparse
import pandas as pd
from tqdm import tqdm
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from config.config import (
    INPUT_DIR, CSV_OUTPUT_DIR, TEMP_DIR, INPUT_CSV_FILE, OUTPUT_CSV_FILE,
    LON_FIELD, LAT_FIELD, PID_FIELD, STREET_VIEW_CONFIG, BATCH_SIZE, BATCH_DELAY
)
from utils.logger import logger, log_exception
from utils.file_io import read_csv, save_csv, load_progress, save_progress
from core.coordinate import wgs2bd09mc
from core.meta_data import get_panorama_id, get_panorama_metadata
from core.street_view import download_directional_images
from core.panorama import download_panorama


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='百度街景爬虫')

    parser.add_argument('--input', type=str, default=INPUT_CSV_FILE,
                        help=f'输入CSV文件名 (默认: {INPUT_CSV_FILE})')

    parser.add_argument('--output', type=str, default=OUTPUT_CSV_FILE,
                        help=f'输出CSV文件名 (默认: {OUTPUT_CSV_FILE})')

    parser.add_argument('--year', type=str, default=STREET_VIEW_CONFIG['year'],
                        help='指定街景年份 (默认: 最新)')

    parser.add_argument('--mode', type=str, choices=['directional', 'panoramic'],
                        default='directional' if STREET_VIEW_CONFIG['use_directional'] else 'panoramic',
                        help='图片下载模式: directional(四方向街景) 或 panoramic(全景图)')

    parser.add_argument('--heading', type=str, choices=['movedir', 'absolute'],
                        default='movedir' if STREET_VIEW_CONFIG['use_move_dir'] else 'absolute',
                        help='Heading计算方式: movedir(根据行驶方向) 或 absolute(绝对角度)')

    parser.add_argument('--batch', type=int, default=BATCH_SIZE,
                        help=f'批处理大小 (默认: {BATCH_SIZE})')

    parser.add_argument('--resume', action='store_true',
                        help='从上次中断处继续爬取')

    return parser.parse_args()


def process_sample_point(row, use_directional=True, use_move_dir=True, target_year=None):
    """处理单个采样点

    Args:
        row: 包含采样点数据的Series
        use_directional: 是否使用四方向街景图
        use_move_dir: 是否根据移动方向计算heading
        target_year: 目标年份

    Returns:
        dict: 处理结果数据
    """
    result = {}

    try:
        pid = row[PID_FIELD]
        lon = row[LON_FIELD]
        lat = row[LAT_FIELD]

        logger.info(f"Processing sample point {pid}: ({lon}, {lat})")

        # 转换坐标
        bd_x, bd_y = wgs2bd09mc(lon, lat)

        if bd_x is None or bd_y is None:
            logger.warning(f"Coordinate conversion failed for {pid}")
            result = {
                'BD_ID': None,
                'BD_MoveDir': None,
                'BD_Content': None,
                'process_status': 'coordinate_failure'
            }
            return result

        # 获取全景图ID
        panorama_id = get_panorama_id(bd_x, bd_y)

        if not panorama_id:
            logger.warning(f"No panorama found for {pid}")
            result = {
                'BD_ID': None,
                'BD_MoveDir': None,
                'BD_Content': None,
                'process_status': 'no_panorama'
            }
            return result

        # 获取全景图元数据
        new_id, move_dir, content = get_panorama_metadata(panorama_id, target_year)

        if not new_id or not content:
            logger.warning(f"Failed to get metadata for {pid}")
            result = {
                'BD_ID': panorama_id,
                'BD_MoveDir': None,
                'BD_Content': None,
                'process_status': 'metadata_failure'
            }
            return result

        # 下载图片
        image_paths = []
        if use_directional:
            # 下载四方向街景图
            image_paths = download_directional_images(new_id, move_dir, pid, lon, lat, use_move_dir)
        else:
            # 下载全景图
            panorama_path = download_panorama(new_id, pid, lon, lat, STREET_VIEW_CONFIG['panorama_zoom'])
            if panorama_path:
                image_paths = [panorama_path]

        # 准备结果
        result = {
            'BD_ID': new_id,
            'BD_MoveDir': move_dir,
            'BD_Content': str(content),
            'BD_ImagePaths': ','.join(image_paths) if image_paths else '',
            'process_status': 'success' if image_paths else 'image_failure'
        }

        return result
    except Exception as e:
        log_exception(e, f"Error processing sample point {row.get(PID_FIELD, 'unknown')}")
        result = {
            'BD_ID': None,
            'BD_MoveDir': None,
            'BD_Content': None,
            'process_status': f'error: {str(e)[:100]}'
        }
        return result


def main():
    """主函数"""
    args = parse_args()

    logger.info("=== 百度街景爬虫开始运行 ===")
    logger.info(f"输入文件: {args.input}")
    logger.info(f"输出文件: {args.output}")
    logger.info(f"模式: {args.mode}")
    logger.info(f"Heading计算: {args.heading}")
    logger.info(f"目标年份: {args.year if args.year else '最新'}")

    try:
        # 读取输入CSV文件
        input_path = INPUT_DIR / args.input
        df = read_csv(input_path)

        # 检查必要的字段
        for field in [PID_FIELD, LON_FIELD, LAT_FIELD]:
            if field not in df.columns:
                logger.error(f"Required field '{field}' not found in input file")
                return

        # 准备输出文件
        output_path = CSV_OUTPUT_DIR / args.output
        progress_path = TEMP_DIR / f"{args.output}.progress"

        # 如果继续上次爬取，加载进度
        processed_pids = set()
        if args.resume and os.path.exists(output_path):
            logger.info("继续上次爬取任务")
            # 读取已处理的记录
            processed_df = read_csv(output_path)
            if PID_FIELD in processed_df.columns:
                processed_pids = set(processed_df[PID_FIELD].astype(str))
            else:
                processed_pids = load_progress(progress_path)

            logger.info(f"已处理 {len(processed_pids)} 个采样点")

        # 筛选未处理的记录
        df['_pid_str'] = df[PID_FIELD].astype(str)
        if processed_pids:
            unprocessed_df = df[~df['_pid_str'].isin(processed_pids)]
        else:
            unprocessed_df = df

        total_points = len(unprocessed_df)
        logger.info(f"需要处理 {total_points} 个采样点")

        if total_points == 0:
            logger.info("没有需要处理的采样点，退出程序")
            return

        # 初始化结果DataFrame
        if args.resume and os.path.exists(output_path):
            result_df = read_csv(output_path)
        else:
            result_df = pd.DataFrame()

        # 设置处理参数
        use_directional = args.mode == 'directional'
        use_move_dir = args.heading == 'movedir'

        # 分批处理
        for i in range(0, total_points, args.batch):
            batch_df = unprocessed_df.iloc[i:i + args.batch]
            logger.info(
                f"处理批次 {i // args.batch + 1}/{(total_points - 1) // args.batch + 1}，共 {len(batch_df)} 条记录")

            batch_results = []

            # 使用tqdm显示进度
            for _, row in tqdm(batch_df.iterrows(), total=len(batch_df), desc="处理进度"):
                # 处理单个采样点
                result = process_sample_point(
                    row,
                    use_directional=use_directional,
                    use_move_dir=use_move_dir,
                    target_year=args.year
                )

                # 将原始数据与新结果合并
                row_result = {**row.to_dict(), **result}
                batch_results.append(row_result)

                # 记录已处理的ID
                processed_pids.add(row['_pid_str'])

                # 保存进度
                save_progress(processed_pids, progress_path)

            # 合并批次结果
            batch_result_df = pd.DataFrame(batch_results)

            # 添加到总结果
            if result_df.empty:
                result_df = batch_result_df
            else:
                result_df = pd.concat([result_df, batch_result_df], ignore_index=True)

            # 保存当前结果
            save_csv(result_df, output_path)
            logger.info(f"已保存 {len(result_df)} 条结果到 {output_path}")

            # 批次间延迟
            if i + args.batch < total_points:
                logger.info(f"批次间延迟 {BATCH_DELAY} 秒...")
                time.sleep(BATCH_DELAY)

        # 处理完成，删除临时进度文件
        if os.path.exists(progress_path):
            os.remove(progress_path)

        logger.info(f"=== 百度街景爬虫运行完成 ===")
        logger.info(f"总共处理了 {len(result_df)} 条记录")

        # 统计处理状态
        if 'process_status' in result_df.columns:
            status_counts = result_df['process_status'].value_counts()
            logger.info("处理状态统计:")
            for status, count in status_counts.items():
                logger.info(f"  {status}: {count}")

    except Exception as e:
        log_exception(e, "程序执行过程中发生错误")
        sys.exit(1)


if __name__ == "__main__":
    main()