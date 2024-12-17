'''
郴州市政府
- 全量爬虫，过往所有数据
新闻列表页URL:https://www.czs.gov.cn/html/dtxx/zwdt/zwyw/default_1.htm
'''
import requests
from lxml import etree
from urllib.parse import urljoin
from datetime import datetime
from fake_useragent import UserAgent
from pymysql.err import IntegrityError
from mytools.tools import retry
from mytools.db_toolbox import SQLHelper

# 已经全部 加1 处理
plate_name = {
    'zwyw':('政务要闻', 451),
    'bmdt': ('部门动态', 2416),
    'qxdt':('区县动态', 2851),
    # 'jrgg':('今日关注', 10), - 已抓完
}

url_list = {
    'zwyw':'https://www.czs.gov.cn/html/dtxx/zwdt/zwyw/default.jsp?jsp.offset={}&jsp.desc=false',  # 政务要闻
    'bmdt':'https://www.czs.gov.cn/html/dtxx/zwdt/bmdt/default.jsp?jsp.offset={}&jsp.desc=false',  # 部门动态
    'qxdt':'https://www.czs.gov.cn/html/dtxx/zwdt/xsqdt/default.jsp?jsp.offset={}&jsp.desc=false',  # 区县动态
    # 'jrgg':'https://www.czs.gov.cn/html/dtxx/11711/default_{}.htm',  # 今日关注  2page -> default_1  - 已抓完
}

db = SQLHelper()

# # 列表页
# index_list_page_url = 'https://www.czs.gov.cn/html/dtxx/zwdt/zwyw/default.htm'  # 第一页
# news_list_page_url = 'https://www.czs.gov.cn/html/dtxx/zwdt/zwyw/default_{}.htm'  # 翻页替换url
#
# # 详情页url统一前缀
# detail_prefix_url = 'https://www.czs.gov.cn/html/dtxx/zwdt/zwyw/'

# headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
}


@retry(max_retries=3, delay=3)
def get_response(url):
    ua = UserAgent()
    headers['User-Agent'] = ua.random
    response = requests.get(url, headers=headers)  # 使用requests 模拟发起get请求，获取网页报文
    # 设置内容编码格式 防止中文乱码
    response.encoding = response.apparent_encoding
    # 判断状态码是否 200  200表示请求成功
    if response.status_code == 200:
        return response
    raise Exception(f"get_response - url请求失败，状态码: {response.status_code}")


# 请求列表页 获取所有新闻详情页url
def parse_list_page(url):
    response = get_response(url)
    doc = etree.HTML(response.text)
    # 使用xpath解析器解析网页源代码 提取网页元素
    # title = doc.xpath('//div[@class="yaowennr-box"]//li/a/@title')  # 提取标题
    hrefs = doc.xpath('//div[@class="yaowennr-box"]//li/a/@href')  # 提取详情页链接
    href_list = []
    for href in hrefs:
        if 'http' not in href:
            href = urljoin(response.url, href)
        if 'czs' in href:
            href_list.append(href)
    return href_list


def parse_detail_page(url,pname):
    response = get_response(url)
    doc = etree.HTML(response.text)
    try:
        # 使用xpath解析器解析网页源代码 提取网页元素
        new_title = doc.xpath('//div[@class="zhengcebiaoti"]//text()')[0]  # 标题
        release_time = doc.xpath('//div[@class="fabushijian"]//text()')[0]  # 发表时间
        publish_source = doc.xpath('//div[@class="fabulaiyuan"]//text()')[0]  # 来源
        content = doc.xpath('//div[@class="wjnerong"]//text()')  # 正文内容
        content = ''.join(content)  # 拼接新闻正文内容
        # 去除非必要字符
        content = content.replace('\n', '').replace('\r', '').replace('\t', '').replace('\u3000', '')  # 拼接新闻正文内容
        # content = content.replace('\t', '').replace('\u3000', '')  # 拼接新闻正文内容
    except Exception as e:
        print(f"数据解析异常，异常原因：{e}！")
        return None

    item = {}
    item['plate_name'] = pname
    item['title'] = new_title
    item['publish_source'] = publish_source
    item['release_time'] = release_time.strip().split(' ')[1]
    item['url'] = url
    item['content'] = content
    item['ctime'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return item


def save_data(data):
    print(data)
    sql = 'insert into shizhenfu(plate_name,title,source,release_time,url,content,ctime) values(%s,%s,%s,%s,%s,%s,%s)'
    try:
        results = db.insert_one(sql, list(data.values()))
    except IntegrityError:
        print('重复数据，已经采集过！')


def main(index_url,pname):
    try:
        detail_page_urls = parse_list_page(index_url)
        for detail_page_url in detail_page_urls:
            data = parse_detail_page(detail_page_url,pname)
            save_data(data)
    except Exception as e:
        print("请更换代理后再试！")
        print(e)

def start():
    for key,url in url_list.items():
        pname = plate_name[key][0]  # 板块名称
        pnumber = plate_name[key][1]  # 翻页参数
        # pnumber = 2  # test 翻页参数
        if key == 'jrgg':
            for page in range(1, pnumber):
                new_url = url.format(page)
                print(f'当前板块：【{pname}】,正在抓取第【{page}】页')
                print(new_url)
                main(new_url,pname)
        else:
            for page in range(0, pnumber,15):
                new_url = url.format(page)
                print(f'当前板块：【{pname}】,正在抓取第【{page}】页')
                print(new_url)
                main(new_url,pname)



if __name__ == '__main__':
    start()
