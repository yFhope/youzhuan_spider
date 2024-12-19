'''
新浪微博
-全量爬虫
-所有关键词的全量数据
['郴州','高椅岭','东江湖','仰天湖','郴州酒店','郴州鱼粉','杀猪粉',]
'''

import re
import time
import random
import pymysql
import requests
import urllib.parse
from jsonpath import jsonpath
from datetime import datetime

from mytools.db_toolbox import SQLHelper
from pymysql.err import IntegrityError


class WeiBo:
    def __init__(self,search_key):
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
            'id': '5073672622309959',
            'mid': '5073672622309959',
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
        self.level_1_comments()


if __name__ == '__main__':
    weibo = WeiBo("key")
    weibo.main()
