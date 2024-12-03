import time
import functools


# 用于错误自动重试
def retry(max_retries=3, delay=1):
    """
    错误重试装饰器
    :param max_retries: 最大重试次数
    :param delay: 每次重试前的延迟时间（秒）
    :return: 装饰器函数
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    print(f"尝试 {attempt} 失败: {e}， {delay} 秒后重试...")  # Retrying in 3 seconds
                    time.sleep(delay)
            # 如果最大重试次数用完后依然抛出异常，则抛出最后捕获的异常
            print(f"All {max_retries} attempts failed.")
            raise last_exception

        return wrapper

    return decorator
