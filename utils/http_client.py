# utils/http_client.py
import time
import requests
import random
import json
from urllib.parse import urlparse, parse_qs
from requests.exceptions import RequestException, Timeout, ConnectionError

from config.config import HTTP_CONFIG
from utils.logger import logger, log_exception


class HttpClient:
    """HTTP请求客户端"""

    def __init__(self, max_retries=None, retry_delay=None, timeout=None, headers=None):
        self.max_retries = max_retries or HTTP_CONFIG['max_retries']
        self.retry_delay = retry_delay or HTTP_CONFIG['retry_delay']
        self.timeout = timeout or HTTP_CONFIG['timeout']
        self.headers = headers or HTTP_CONFIG['headers'].copy()
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get(self, url, params=None, headers=None, stream=False):
        """发送GET请求"""
        retry_count = 0
        merged_headers = self.headers.copy()
        if headers:
            merged_headers.update(headers)

        while retry_count <= self.max_retries:
            try:
                logger.debug(f"Sending GET request to {url}")
                response = self.session.get(
                    url,
                    params=params,
                    headers=merged_headers,
                    timeout=self.timeout,
                    stream=stream
                )
                if response.status_code == 200:
                    return response
                else:
                    logger.warning(f"HTTP request failed with status code {response.status_code}: {url}")
            except (ConnectionError, Timeout) as e:
                log_exception(e, f"Connection error on attempt {retry_count + 1}/{self.max_retries + 1}")
            except RequestException as e:
                log_exception(e, f"Request error on attempt {retry_count + 1}/{self.max_retries + 1}")

            retry_count += 1
            if retry_count <= self.max_retries:
                # 增加随机延迟，避免被检测为爬虫
                sleep_time = self.retry_delay * (1 + random.random())
                logger.info(f"Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)

        raise RequestException(f"Failed to get {url} after {self.max_retries} retries")

    def get_json(self, url, params=None, headers=None):
        """发送GET请求并解析JSON响应"""
        response = self.get(url, params, headers)
        content = response.text

        # 处理JSONP格式
        if content.startswith('/**/jsonp.'):
            # 提取JSON部分
            json_str = content[content.find('(') + 1:content.rfind(')')]
            return json.loads(json_str)

        try:
            return response.json()
        except ValueError as e:
            log_exception(e, "Failed to parse JSON response")
            raise

    def get_image(self, url, params=None, headers=None):
        """获取图片内容"""
        response = self.get(url, params, headers, stream=True)
        return response.content


# 创建全局HTTP客户端实例
http_client = HttpClient()