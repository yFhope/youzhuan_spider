'''
郴州市政府
- 全量爬虫，过往所有数据
新闻列表页URL:https://www.czs.gov.cn/html/dtxx/zwdt/zwyw/default_1.htm
'''
import time
import functools

import requests
from lxml import etree


# 列表页
index_list_page_url = 'https://www.czs.gov.cn/html/dtxx/zwdt/zwyw/default.htm'  # 第一页
news_list_page_url = 'https://www.czs.gov.cn/html/dtxx/zwdt/zwyw/default_{}.htm' # 翻页替换url

# 详情页url统一前缀
detail_prefix_url = 'https://www.czs.gov.cn/html/dtxx/zwdt/zwyw/'
# headers
headers = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
}

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
                    print(f"尝试 {attempt} 失败: {e}， {delay} 秒后重试...")   # Retrying in 3 seconds
                    time.sleep(delay)
            # 如果最大重试次数用完后依然抛出异常，则抛出最后捕获的异常
            print(f"All {max_retries} attempts failed.")
            raise last_exception
        return wrapper
    return decorator

@retry(max_retries=3, delay=3)
def get_response(url):
    #  使用requests 模拟发起get请求，获取网页报文
    response = requests.get(url, headers=headers)
    # 设置内容编码格式 防止中文乱码
    response.encoding = response.apparent_encoding
    # 判断状态码是否 200  200表示请求成功
    if response.status_code == 200:
        return response
    raise Exception(f"get_response - url请求失败，状态码: {response.status_code}")

# 请求列表页 获取所有新闻详情页url
def list_page(url):
    response = get_response(url)
    doc = etree.HTML(response.text)
    # 使用xpath解析器解析网页源代码 提取网页元素
    # title = doc.xpath('//div[@class="yaowennr-box"]//li/a/@title')  # 提取标题
    hrefs = doc.xpath('//div[@class="yaowennr-box"]//li/a/@href')  # 提取详情页链接
    new_hrefs = []
    for href in hrefs:
        # 过滤掉转发新闻数据 方便后续处理
        if 'http' not in href:
            href = detail_prefix_url + href
            new_hrefs.append(href)
    print(new_hrefs)
    return new_hrefs

def parse_detail_page(url):
    response = get_response(url)
    doc = etree.HTML(response.text)
    # 使用xpath解析器解析网页源代码 提取网页元素
    new_title = doc.xpath('//div[@class="zhengcebiaoti"]//text()')  # 标题
    release_time = doc.xpath('//div[@class="fabushijian"]//text()')  # 发表时间
    publish_source = doc.xpath('//div[@class="fabulaiyuan"]//text()')  # 来源
    content = doc.xpath('//div[@class="wjnerong"]//text()')  # 正文内容
    content = ''.join(content)  # 拼接新闻正文内容
    # 去除非必要字符
    content = content.replace('\n', '').replace('\r', '').replace('\t', '').replace('\u3000', '')  # 拼接新闻正文内容
    # content = content.replace('\t', '').replace('\u3000', '')  # 拼接新闻正文内容
    item = {}
    item['new_title'] = new_title
    item['release_time'] = release_time
    item['publish_source'] = publish_source
    item['content'] = content
    return item


def save_data(data):
    # 后期需要存储到数据库，这里示例先存储到本地
    title = data['new_title'][0]
    release_time = data['release_time'][0]
    content = data['content']
    print(f"正在保存新闻：【{title}】")
    file_name = title
    with open(f'news/{file_name}.txt', 'a',encoding='utf-8') as f:
        f.write(content)
    f.close()

def main():
    try:
        detail_page_urls = list_page(index_list_page_url)
        for detail_page_url in detail_page_urls:
            data = parse_detail_page(detail_page_url)
            save_data(data)
    except Exception as e:
        print("请更换代理后再试！")
        print(e)


if __name__ == '__main__':
    main()