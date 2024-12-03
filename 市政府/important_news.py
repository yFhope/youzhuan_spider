'''
郴州市政府 - 政务要闻板块
新闻列表页URL:https://www.czs.gov.cn/html/dtxx/zwdt/zwyw/default_1.htm

'''
import requests

# 列表页
news_list_page_url = 'https://www.czs.gov.cn/html/dtxx/zwdt/zwyw/default_1.htm'
# 详情页url统一前缀
detail_prefix_url = 'https://www.czs.gov.cn/html/dtxx/zwdt/zwyw/'
# headers
headers = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
}

def retry(max_retries=3, delay=1, exceptions=(Exception,)):
    """
    错误重试装饰器
    :param max_retries: 最大重试次数
    :param delay: 每次重试前的延迟时间（秒）
    :param exceptions: 捕获的异常类型（默认为 Exception）
    :return: 装饰器函数
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    print(f"Attempt {attempt} failed: {e}. Retrying in {delay} seconds...")
                    time.sleep(delay)
            # 如果最大重试次数用完后依然抛出异常，则抛出最后捕获的异常
            print(f"All {max_retries} attempts failed.")
            raise last_exception

        return wrapper

    return decorator


def get_response(url):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response
    raise "get_response - url请求失败"

def listpage():
    pass