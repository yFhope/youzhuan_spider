'''
新浪微博
-全量爬虫
-所有关键词的全量数据
['郴州','高椅岭','东江湖','仰天湖','郴州酒店','郴州鱼粉','杀猪粉',]
'''

import re
import time
import random
from itertools import count

import pymysql
import requests
import urllib.parse
from jsonpath import jsonpath
from datetime import datetime

from mytools.db_toolbox import SQLHelper
from pymysql.err import IntegrityError


class WeiBo:
    def __init__(self, search_key):
        # 首页（搜索页）接口信息
        self.url = 'https://m.weibo.cn/api/container/getIndex'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1',
            'Referer': 'https://m.weibo.cn/detail/4813628149072458',
            'cookie': '_T_WM=11581596339; WEIBOCN_FROM=1110003030; SCF=AiJsIR89CSyo1Ywjtc-RkKphdKcdnTYJRyAWlj0RBrIWK5cHAlhz1rRCGLKvMwJXYp869OozhF1TbAtXyRKiWZA.; SUB=_2A25KZQfwDeRhGeBM4lQX-SjJwjiIHXVpGwU4rDV6PUJbktAbLXmmkW1NRLngcRHL5Yut8Kw0tp9DY9-QcYjlNQID; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WWVQlloI5dKA59HvZPKfPwF5NHD95Qceo.cSo.cSK.XWs4DqcjMi--NiK.Xi-2Ri--ciKnRi-zNSoz4Soq4So-4S5tt; SSOLoginState=1734440864; ALF=1737032864; MLOGIN=1; XSRF-TOKEN=10fcd2; mweibo_short_token=f8fe1cdb01; M_WEIBOCN_PARAMS=oid%3D5083703672049076%26luicode%3D20000061%26lfid%3D5083703672049076%26uicode%3D20000061%26fid%3D5083703672049076'
        }

        self.xchead = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1',
        }

        # self.search_key = input('请输入你要检索的微博词汇:')
        self.data = {
            'containerid': f'100103type=1&q={search_key}',
            'page_type': 'searchall',
            'page': None
        }

        # 一级评论的接口信息
        self.first_url = 'https://m.weibo.cn/comments/hotflow'
        self.level1_data = {
            'id': '4813628149072458',
            'mid': '4813628149072458',
            'max_id': None,
            'max_id_type': '0'
        }

        # 二级评论的接口信息
        self.second_url = 'https://m.weibo.cn/comments/hotFlowChild'
        self.level2_data = {
            'cid': '4813643344774141',
            'max_id': '0',
            'max_id_type': '0'
        }

        # 板块名称&对应的url
        self.navbar_name_url_item = {}

        # 数据库
        self.db = SQLHelper()
        self.search_key = search_key

    # 提取导航栏 板块名称&对应的url
    def get_navbar(self):
        response = requests.get(self.url, params=self.data, headers=self.headers)
        if response.status_code == 200:
            json_data = response.json()
            navbar_names = jsonpath(json_data, '$..channel_list[1:11]..name')
            navbar_schemes = jsonpath(json_data, '$..channel_list[1:11]..scheme')
            # 建立一个空字典对象
            for name, scheme in zip(navbar_names, navbar_schemes):
                # 二次处理url信息，替换链接头
                new_str = 'https://m.weibo.cn/api/container/getIndex'
                _, query_string = scheme.split('?', 1)

                if name == '综合':
                    split_point = query_string.find('type')
                    prefix = query_string[:split_point + len('type')]
                    to_encode = query_string[split_point + len('type'):]
                    query_string = prefix + urllib.parse.quote(to_encode)

                self.navbar_name_url_item[name] = new_str + '?' + query_string

    # 微博 实时板块 接口
    def real_time_api(self, page_number=None):
        url = self.navbar_name_url_item['实时']  # 实时 综合
        params = {
            'page_type': 'searchall',
            'page': page_number,
        }
        while True:
            response = requests.get(url, params=params, headers=self.headers)
            page = params['page']
            print(f'正在抓取第{page}页，', response.url)
            page_number = 0
            if response.status_code == 200:
                json_data = response.json()
                # 获取下一页翻页参数
                page_number = jsonpath(json_data, '$..cardlistInfo.page')
                page_number = page_number[0] if page_number else 0
                # 微博正文主体内容+微博发布者信息
                cards = jsonpath(json_data, '$..cards')
                for card in cards[0]:
                    try:
                        release_time = jsonpath(card, '$..mblog..created_at')[0]  # 发表微博的时间
                        r_time = datetime.strptime(release_time, "%a %b %d %H:%M:%S %z %Y")

                        uname = jsonpath(card, '$..mblog..screen_name')[0]  # 发表微博的用户昵称
                        gender = jsonpath(card, '$..mblog..gender')[0]  # 发表微博的用户性别 m-男 f-女
                        followers = jsonpath(card, '$..mblog..followers_count')[0]  # 用户粉丝数
                        follow_count = jsonpath(card, '$..mblog..follow_count')[0]  # 用户关注数 关注了多少人
                        source = jsonpath(card, '$..mblog.source')[0]  # 发表微博的设备信息
                        comments = jsonpath(card, '$..mblog..comments_count')[0]  # 微博的评论数
                        attitudes = jsonpath(card, '$..mblog..attitudes_count')[0]  # 微博的点赞数
                        reposts = jsonpath(card, '$..mblog..reposts_count')[0]  # 微博的转发数

                        status_country = jsonpath(card, '$..mblog..status_country')  # 用户IP所在国家
                        status_province = jsonpath(card, '$..mblog..status_province')  # 用户IP所在省
                        status_country = status_country[0] if status_country else ''
                        status_province = status_province[0] if status_province else ''

                        text_length = jsonpath(card, '$..mblog.textLength')  # 正文文本长度
                        text_length = text_length[0] if text_length else None
                        weibo_text = jsonpath(card, '$..mblog.text')[0]  # 微博正文内容
                        weibo_text = re.sub('<.*?>', '', weibo_text)  # 替换表情符号

                        # 跟进抓取评论信息用
                        blog_id = jsonpath(card, '$..mblog.id')[0]  # 发表微博 文章的ID
                    except Exception as e:
                        print("数据解析错误---->>>", e)
                        continue

                    try:
                        #  存储入库
                        sql = '''insert into weibo_mainbody(
                                             blog_id,user_name,gender,followers_count,follow_count,sources,
                                             comments_count,attitudes_count,reposts_count,release_time,status_country,
                                             status_province,weibo_text,weibo_textLength,search_key) 
                                 values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
                        qdata = (blog_id, uname, gender, followers, follow_count, source, comments, attitudes, reposts,
                                 r_time, status_country, status_province, weibo_text, text_length, self.search_key)
                        result = self.db.insert_one(sql, qdata)
                        print(blog_id, "入库成功" if result else "入库失败")
                        print(qdata)
                        print('---' * 50)

                        # 获取一级评论
                        # self.level1_data['id'] = blog_id
                        # self.level1_data['mid'] = blog_id
                        # self.level_1_comments()
                    except IntegrityError:
                        print("重复入库，不处理")

            # 下一次循环前更新翻页参数
            # 上一页的微博、评论获取完毕之后，开始翻页 大于1 小于50
            if 1 < page_number < 50:
                params['page'] = page_number
                time.sleep(random.uniform(3, 7))
            else:
                print('====实时动态已获取完毕====')  # 虽然不太可能运行到这里，但改写还是得写
                break

    # 获取level_1_comments
    def level_1_comments(self):
        try:  # 有可能没有一级评论，所以这次也要添加异常处理
            while True:
                response = requests.get(self.first_url, params=self.level1_data, headers=self.headers)
                # 根据网页数据包结构，获取以及评论的内容以及评论者
                names = jsonpath(response.json(), '$..data[:].user.screen_name')
                texts = jsonpath(response.json(), '$..data[:].text')
                # 获取一级评论的cid，以匹配二级评论。放入for循环中遍历
                cids = jsonpath(response.json(), '$..data[:].rootid')
                for name, text, cid in zip(names, texts, cids):
                    new_name = re.sub('<.*?>', '', name)  # 正则处理表情包
                    new_text = re.sub('<.*?>', '', text)  # 正则处理表情包
                    print(f'\033[1;32m\t\t{new_name} --1--> {new_text}\033[0m')  # 绿色效果打印

                    # 调用二级评论接口
                    time.sleep(random.uniform(1, 7))
                    try:  # 异常处理：如果没有二级评论还调用二级方法，json()解析不到数据就会报错：requests.exceptions.JSONDecodeError
                        self.level2_data['cid'] = cid
                        self.level_2_comments()
                    except Exception as e:
                        # print('\t\t\t--------没有二级评论--------')
                        print(f'\033[1;31m\t\t\t\t--------没有二级评论--------\033[0m')  # 效果红色打印

                # 1级评论接口 翻页 获取网页max_id作为下一页的翻页参数
                max_id = jsonpath(response.json(), '$..data.max_id')[0]
                if max_id == 0:
                    print(f'\033[1;32m一级评论已全部获取完毕\033[0m')  # 绿色效果打印
                    break
                # 下一次循环前更新翻页接口参数
                self.level1_data['max_id'] = max_id
                time.sleep(random.uniform(3, 9))
        except:
            print(f'\033[1;31m\t\t========没有一级评论========\033[0m')  # 红色效果打印

    # 获取二级评论
    def level_2_comments(self):
        # 循环 - 更新参数  - 翻页 - 简单模式
        while True:
            response = requests.get(self.second_url, params=self.level2_data, headers=self.headers)
            user_names = jsonpath(response.json(), '$..data[:].user.screen_name')
            comment_texts = jsonpath(response.json(), '$..data[:].text')
            # 遍历处理每一条二级用户评论数据
            for uname, ctext in zip(user_names, comment_texts):
                new_ctext = re.sub('<.*?>', '', ctext)  # 正则处理表情包
                print('\t\t\t\t', uname, '--2-->', new_ctext)

            # 获取二级网页max_id作为下一页的翻页参数
            second_max_id = jsonpath(response.json(), '$..max_id')[0]
            # max_id=0 时翻页结束，不等于0才递归
            if second_max_id in [0, 186494897570]:  # 第一条评论的最后一条跟评的数据报的max_id不知道怎么会使变了，所以只能加进来，否则程序报错
                print('\t\t\t\t=========二级评论获取完毕=========')
                self.level2_data['max_id'] = 0
                break
            # 下一次循环前更新翻页接口参数
            self.level2_data['max_id'] = second_max_id
            time.sleep(random.uniform(2, 8))

    def main(self):
        self.get_navbar()
        self.real_time_api()
        # self.real_time_api(49)


if __name__ == '__main__':
    key_list = ['高椅岭', '郴州', '东江湖', '仰天湖', '郴州酒店', '郴州鱼粉', '杀猪粉', ]
    for key in key_list[4:]:
        weibo = WeiBo(key)
        weibo.main()
