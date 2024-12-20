
'''
分析：
微博移动端接口需要登录才能爬取，采用cookie登录方式
移动端静态访问接口:https://m.weibo.cn/detail/4813628149072458  (切换成移动端后再浏览器导航栏访问即可)
一级评论接口：
    -- 完整URL:
        https://m.weibo.cn/comments/hotflow?id=4820842020078095&mid=4820842020078095&max_id_type=0
    -- 请求参数：
        id: 4820842020078095   博主ID
        mid: 4820842020078095
        max_id_type: 0
        max_id: 82512885133612，当翻页的时候会出现max_id，该参数为翻页ID，在上一页数据包里可以找到
二级评论接口：
    -- 完整URL:
        https://m.weibo.cn/comments/hotFlowChild?cid=4820898417480815&max_id=0&max_id_type=0
    -- 请求参数：
        cid: 4820898417480815  跟评ID（谁的跟评）
        max_id: 0  跟评翻页ID
        max_id_type: 0

一级标题 一级标题翻页
二级标题 二级标题翻页
'''
from datetime import datetime

import requests
from jsonpath import jsonpath
import time
import re
import sys
import time
import random
from loguru import logger
from pymysql.err import IntegrityError


from mytools.db_toolbox import SQLHelper


class WeiBoCommentSpider(object):
    def __init__(self,level_1_bid='5073672622309959'):
        self.blog_id = level_1_bid
        # 一级评论接口信息
        self.one_url = 'https://m.weibo.cn/comments/hotflow'
        self.level_1_params = {
            'id': level_1_bid,
            'mid': level_1_bid,
            'max_id_type': '0',
            'max_id': None  # 一级 翻页ID  （第一页无该参数 所以赋值为None）
        }
        # https://m.weibo.cn/detail/4865363672566456 测试
        # 二级评论接口信息
        self.two_url = 'https://m.weibo.cn/comments/hotFlowChild'
        self.level_2_params = {
            'cid': '4879471498232275',  # 跟评ID
            'max_id': '0',  # 翻页ID
            'max_id_type': '0'
        }
        self.headers = {
            # 'Referer': 'https://m.weibo.cn/detail/4864041232896092',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
            'cookie': '_T_WM=11581596339; WEIBOCN_FROM=1110003030; SCF=AiJsIR89CSyo1Ywjtc-RkKphdKcdnTYJRyAWlj0RBrIWK5cHAlhz1rRCGLKvMwJXYp869OozhF1TbAtXyRKiWZA.; SUB=_2A25KZQfwDeRhGeBM4lQX-SjJwjiIHXVpGwU4rDV6PUJbktAbLXmmkW1NRLngcRHL5Yut8Kw0tp9DY9-QcYjlNQID; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WWVQlloI5dKA59HvZPKfPwF5NHD95Qceo.cSo.cSK.XWs4DqcjMi--NiK.Xi-2Ri--ciKnRi-zNSoz4Soq4So-4S5tt; SSOLoginState=1734440864; ALF=1737032864; MLOGIN=1; XSRF-TOKEN=10fcd2; mweibo_short_token=f8fe1cdb01; M_WEIBOCN_PARAMS=oid%3D5083703672049076%26luicode%3D20000061%26lfid%3D5083703672049076%26uicode%3D20000061%26fid%3D5083703672049076'
        }
        self.db = SQLHelper()

    def insert_to_db(self,qdata):
        sql = '''insert into weibo_comments(blog_id, user_id,user_name, gender, followers_count,
                                                            follow_count,comment_text, created_at, rootid,level) 
                                 values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
        result = 0
        try:
            result = self.db.insert_one(sql, qdata)
        except IntegrityError:
            pass
        return result

    # 1，请求并解析一级评论
    def level_1_comments(self, url, data):
        logger.info(f'====================={self.blog_id} -- 开始抓取一级评论=====================')
        response = requests.get(url, headers=self.headers, params=data)
        level = 1
        if response.status_code == 200:
            comment_datas = jsonpath(response.json(),'$..data.data')
            if not comment_datas:
                logger.warning('还没有人评论哦~快来抢沙发！')
                return
            for comment_data in comment_datas[0]:
                user_name = jsonpath(comment_data, '$.user.screen_name')[0]  # 评论用户名称
                user_id = jsonpath(comment_data, '$.user.id')[0]  # 评论用户id
                gender = jsonpath(comment_data, '$.user.gender')[0]  # 评论用户性别
                followers_count = jsonpath(comment_data, '$.user.followers_count')[0]  # 评论用户粉丝数
                follow_count = jsonpath(comment_data, '$.user.follow_count')[0]  # 评论用户关注人数

                comment = jsonpath(comment_data, '$.text')  # 一级 评论
                comment = re.sub('<.*?>', '', comment[0])  # 评论 --> 正则处理html 字符
                created_at = jsonpath(comment_data, '$.created_at')[0]  # 评论时间
                created_at = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")

                # 为了获取时知道二级评论来自哪条跟评 需要在一级评论接口中解析rootid（跟评ID）
                cid = jsonpath(comment_data, '$.rootid')  # 评论ID  |  获取1级评论中的跟评ID
                cid = cid[0] if cid else None


                qdata = (self.blog_id, user_id, user_name, gender, followers_count,follow_count,comment, created_at, cid,level)
                print("level ①",qdata)
                self.insert_to_db(qdata)

                # 二级评论-二级评论-二级评论
                #  有些一级评论下无跟评 该异常需要捕捉
                if cid is not None:
                    try:
                        #  切换跟评ID 以此获得每条一级评论下的跟评
                        self.level_2_params['cid'] = cid
                        #  调用解析方法发现 二级评论重复打印
                        self.level_2_comments(self.two_url, self.level_2_params)
                        t = random.randint(3,9)
                        time.sleep(t)
                    except Exception as e:
                        self.level_2_params['max_id'] = 0
                        # print('当前一级评论已无跟评(二级评论)~ 将继续爬取后续一级评论')
                        logger.info(f'====================={self.blog_id} -- level_2 抓取完毕！=====================')
            # 一级评论翻页
            max_id = jsonpath(comment_datas, '$.data.max_id')  # 一级评论 翻页ID
            max_id  = max_id[0] if max_id else 0
            print("当前一级评论翻页ID：", max_id)
            if max_id == 0:
                logger.info(f'====================={self.blog_id} -- level_1 抓取完毕！=====================')
                return
            else:
                # 更新翻页参数
                self.level_1_params['max_id'] = max_id
                # 2.2 递归调用自己 实现翻页爬取
                self.level_1_comments(self.one_url, self.level_1_params)
                t = random.randint(4, 9)
                time.sleep(t)

    # 3，请求二级评论接口并解析二级评论内容
    def level_2_comments(self, url, data):
        logger.info(f'====================={self.blog_id} -- 开始抓取②级评论=====================')
        response = requests.get(url,params=data, headers=self.headers)
        level = 2
        if response.status_code == 200:
            comment_datas = jsonpath(response.json(), '$.data')
            for comment_data in comment_datas[0]:
                user_name = jsonpath(comment_data, '$.user.screen_name')[0]  # 二级 评论用户名称
                user_id = jsonpath(comment_data, '$.user.id')[0]  # 二级评论用户id
                gender = jsonpath(comment_data, '$.user.gender')[0]  # 二级 评论用户性别
                followers_count = jsonpath(comment_data, '$.user.followers_count')[0]  # 二级 评论用户粉丝数
                follow_count = jsonpath(comment_data, '$.user.follow_count')[0]  # 二级 评论用户关注人数

                comment = jsonpath(comment_data, '$.text')  # 二级 评论文本
                comment = re.sub('<.*?>', '', comment[0])  # 评论 --> 正则处理html 字符
                created_at = jsonpath(comment_data, '$.created_at')[0]  # 评论时间
                created_at = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")

                cid = jsonpath(comment_data, '$.rootid')
                root_id = cid[0] if cid else None

                # 二级评论 数据入库
                qdata = (self.blog_id, user_id, user_name, gender, followers_count, follow_count, comment,
                         created_at, root_id,level)
                print("level ②",qdata)
                self.insert_to_db(qdata)


            # 4，开始二级评论翻页
            two_max_id = jsonpath(comment_datas, '$..max_id')  # 解析出翻页ID  健名为max_id
            two_max_id = two_max_id[0] if two_max_id else 0
            # 4.2 因翻页总有翻完的时候，每当当前一级评论下的二级评论全部翻页完成 应当接着翻下一条一级评论的所有跟评
            # 当翻页结束max_id为0
            if two_max_id == 0:
                logger.info(f'====================={self.blog_id} -- level_2 抓取完毕！=====================')
                # 4.3 二级翻页结束之后将max_id恢复为0 便于下一条一级评论翻页爬取
                self.level_2_params['max_id'] = 0
            else:
                # 4.1 切换二级接口翻页参数 且递归调用自己实现二级翻页
                self.level_2_params['max_id'] = two_max_id
                self.level_2_comments(self.two_url, self.level_2_params)
                t = random.randint(5, 9)
                time.sleep(t)

    def main(self):
        self.level_1_comments(self.one_url, self.level_1_params)


if __name__ == '__main__':
    dbc = SQLHelper()
    result = dbc.query_all('select blog_id,search_key from weibo_mainbody where flag=0;')
    for row in result:
        bid = row['blog_id']
        key = row['search_key']
        logger.info(f'正在抓取blog_id->{bid}评论数据,所属关键词：{key}')
        comment = WeiBoCommentSpider(bid)
        comment.main()
        res = dbc.update(f'update weibo_mainbody set flag= 1 where blog_id ={bid};')
        print("更新状态：",res)
