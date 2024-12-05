'''
-时政板块
https://www.czxww.cn/column/node_10003.html
'''

import requests
from lxml import etree
from mytools.tools import retry

# 列表页url
# 翻页规则 -> 2 3 4 元页码+1
index_url = 'https://www.czxww.cn/column/node_10003_{}.html'

custom_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
}

@retry(3,3)
def get_response(url):
    #  使用requests 模拟发起get请求，获取网页报文
    response = requests.get(url, headers=custom_headers)
    # 设置内容编码格式 防止中文乱码
    response.encoding = response.apparent_encoding
    # 判断状态码是否 200  200表示请求成功
    if response.status_code == 200:
        return response
    raise Exception(f"get_response - url请求失败，状态码: {response.status_code}")

# 请求列表页url，返回所有详情页URL
def get_list_page_url(url):
    response = get_response(url)
    doc = etree.HTML(response.text)
    hrefs = doc.xpath('//*[@class="list_ul"]/li/a/@href')
    return hrefs

# 详情页处理
def get_detail_page_data(detail_url):
    '''
    请求详情页，解析网页源码，抓取需要的字段信息
    :param detail_url: 详情页url
    :return: （标题、发表时间、作者、来源、正文内容）
    '''
    try:  # 处理请求异常、解析异常  两种异常形式都没有其余解决方案，返回空-给下一步处理
        response = get_response(detail_url)
        doc = etree.HTML(response.text)  # 把网页源码文本转换成HTML文档对象 方便后续解析
        title = doc.xpath('//*[@class="contPart"]/h1/text()')[0]  # 标题
        author = doc.xpath('//*[@class="contPart"]/div/span[1]/text()')[0]  # 作者
        source = doc.xpath('//*[@class="contPart"]/div/span[2]/text()')[0]  # 来源
        rel_time = doc.xpath('//*[@class="contPart"]/div/span[3]/text()')[0]    # 发布时间
        # 新闻正文
        content = doc.xpath('//div[@class="theText"]//p/text()')
    except Exception as e:
        return None
    content = ''.join(content)
    # 封装数据
    item = {}
    item['title'] = title
    item['author'] = author
    item['source'] = source
    item['rel_time'] = rel_time
    item['content'] = content
    return item

# 存储数据到数据库
def save_data(data):
    print(data)

def start():
    for page_number in range(2, 99999999):  # 翻页
        try:
            lurl = index_url.format(page_number)
            hrefs = get_list_page_url(lurl)
        except Exception as e:
            print(f'异常页码: {page_number}, 全量数据已经抓完或反爬!')
            print(f'异常URL: {lurl}')
            break

        for href in hrefs:  # 遍历每一页中获取的详情页url
            data = get_detail_page_data(href)
            if data is None:
                continue
            save_data(data)
            print('---'*20)


if __name__ == '__main__':
    start()