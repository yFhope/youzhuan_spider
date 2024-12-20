'''
郴州文旅爬虫
- todo 郴州要览 + 通知公告 两个板块爬虫
-  全量爬虫
- 只抓发文数量，不抓详情内容

'''
import requests
from lxml import etree
from datetime import datetime
from fake_useragent import UserAgent
from pymysql.err import IntegrityError

from mytools.tools import retry
from mytools.db_toolbox import SQLHelper

# 列表页url
# index_url = 'http://www.app.czs.gov.cn/lywsj/zwgk/lydt/default.jsp?pager.offset=0&pager.desc=false'

db = SQLHelper()

plate_name = {
    'tzgg':('通知公告',721),
    'czyl':('郴州要览',5091),
    # 'tslm':'xxx',
    # 'wmcj':('文明创建',150),
}

# 通知公告
url_list = {
    'tzgg':'http://www.app.czs.gov.cn/lywsj/zwgk/tzgg/default.jsp?pager.offset={}&pager.desc=false',  # 通知公告
    'czyl':'http://www.app.czs.gov.cn/lywsj/zwgk/lydt/default.jsp?pager.offset={}&pager.desc=false',  # 郴州要览
    # 'tslm':'xxx',
    # 'wmcj':'http://www.app.czs.gov.cn/lywsj/zthd/57126/index.jsp?pager.offset={}&pager.desc=false',   # 文明创建
}

# headers
headers = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
}


@retry(max_retries=3, delay=3)
def get_response(url):
    ua = UserAgent()
    headers['User-Agent'] = ua.random
    response = requests.get(url, headers=headers)
    response.encoding = response.apparent_encoding
    if response.status_code == 200:
        return response
    raise Exception(f"get_response - url请求失败，状态码: {response.status_code}")

def parse_list_page(url):
    response = get_response(url)
    doc = etree.HTML(response.text)
    # 每篇新闻的发布时间
    release_time = doc.xpath('//*[@class="fz-tab"]/table/tbody/tr/td[3]/text()')
    # 获取当前页所有新闻的详情页url  - 用于后续计数
    hrefs = doc.xpath('//*[@class="fz-tab"]/table/tbody/tr//a/@href')
    titles = doc.xpath('//*[@class="fz-tab"]/table/tbody/tr//a/text()')
    item = {}
    item['titles'] = titles
    item['hrefs'] = hrefs
    item['release_time'] = release_time
    return item

def save_data(plate_name,title,href,rtime):
    sql = 'insert into cz_wenlvju(plate_name,title,url,release_time,ctime) values(%s,%s,%s,%s,%s)'
    rtime = datetime.strptime(rtime, "%Y-%m-%d")
    ctime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        db.insert_one(sql,(plate_name,title,href,rtime,ctime))
    except IntegrityError:
        print("数据重复")


def start():
    for key,index_url in url_list.items():
        p_name = plate_name[key][0]
        page_number = plate_name[key][1]
        for offset in range(0,page_number,10):  # 只抓几页做测试
            print("========================================================================================================")
            print("正在抓取：",index_url.format(offset))
            item = parse_list_page(index_url.format(offset))
            for title,href,rtime in zip(item['titles'],item['hrefs'],item['release_time']):
                save_data(p_name,title,href,rtime)



if __name__ == '__main__':
    start()

