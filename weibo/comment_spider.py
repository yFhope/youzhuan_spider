# import requests
# from jsonpath import jsonpath
# import time
# import re
# import sys
# import time
# import random
#
# '''
# 分析：
# 微博移动端接口需要登录才能爬取，采用cookie登录方式
# 移动端静态访问接口:https://m.weibo.cn/detail/4813628149072458  (切换成移动端后再浏览器导航栏访问即可)
# 一级评论接口：
#     -- 完整URL:
#         https://m.weibo.cn/comments/hotflow?id=4820842020078095&mid=4820842020078095&max_id_type=0
#     -- 请求参数：
#         id: 4820842020078095   博主ID
#         mid: 4820842020078095
#         max_id_type: 0
#         max_id: 82512885133612，当翻页的时候会出现max_id，该参数为翻页ID，在上一页数据包里可以找到
# 二级评论接口：
#     -- 完整URL:
#         https://m.weibo.cn/comments/hotFlowChild?cid=4820898417480815&max_id=0&max_id_type=0
#     -- 请求参数：
#         cid: 4820898417480815  跟评ID（谁的跟评）
#         max_id: 0  跟评翻页ID
#         max_id_type: 0
#
# 一级标题 一级标题翻页
# 二级标题 二级标题翻页
# '''
#
# class WeiBo():
#     def __init__(self):
#         # 一级评论及参数
#         self.one_url = 'https://m.weibo.cn/comments/hotflow'
#         self.one_data = {
#             'id': '4813628149072458',  # 博主ID
#             'mid': '4813628149072458',
#             'max_id_type': '0',
#             'max_id': None
#         }
#         # 二级评论
#         self.two_url = 'https://m.weibo.cn/comments/hotFlowChild'
#         self.two_data = {
#             'cid': '',  # 跟评ID（谁的跟评） 在一级评论接口找
#             'max_id': '0',  # 二级评论的翻页ID
#             'max_id_type': '0'
#         }
#
#         self.headers = {
#             'Referer': 'https://m.weibo.cn/detail/4813628149072458?cid=4816884848924963',
#             'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
#             'cookie': 'WEIBOCN_FROM=1110003030; SUB=_2A25OOW6qDeRhGeFK7VIZ9CnNzDmIHXVtwnLirDV6PUJbkdAKLVX_kW1NQyQiyKJQLJ4J-sG9UWMQHg2ebz3YL7hv; _T_WM=29840740578; MLOGIN=1; M_WEIBOCN_PARAMS=oid%3D4820988925575680%26luicode%3D10000011%26lfid%3D102803%26uicode%3D20000061%26fid%3D4820988925575680; XSRF-TOKEN=b158c9'
#         }
#
#     # 请求并解析一级评论
#     def get_one_data(self, url, data):
#         response = requests.get(url, headers=self.headers, params=data)
#         if response.status_code == 200:
#             json_data = response.json()
#             one_name = jsonpath(json_data, '$..data[0:20].user.screen_name')  # 一级评论的作者
#             one_text = jsonpath(json_data, '$..data[0:20].text')  # 一级评论的作者
#             mid = jsonpath(json_data, '$..[0:20].rootid')  # 获取一级评论中的跟评ID
#             for one_names, one_texts, mids in zip(one_name, one_text, mid):
#                 comment = re.sub('<.*?>', '', one_texts)  # 评论 --> 正则处理html 字符
#                 print('----一级评论----')
#                 print(one_names, comment)  # 打印一级评论
#                 print('当前一级评论的跟评ID:', mids)
#                 print('============')
#                 try:
#                     # 有些一级评论下无跟评
#                     self.two_data['cid'] = mids  # 切换跟评ID以获取每一个一级评论下的跟评
#                     self.get_two_data(self.two_url, self.two_data)
#                 except:
#                     print('当前一级评论已无跟评~ 将继续爬取后续一级评论')
#             # 开始翻页爬取一级评论
#             max_id = jsonpath(json_data, '$..data.max_id')[0]  # 一级评论 翻页ID
#             print("当前一级评论翻页ID：", max_id)
#             if max_id == 0:
#                 sys.exit('该用户一级评论已爬取完~')
#             else:
#                 # time.sleep(random.randint(3, 7))
#                 # time.sleep(random.randint(3, 7))
#                 self.one_data['max_id'] = max_id
#                 # 递归调用自己 实现翻页爬取
#                 self.get_one_data(self.one_url, self.one_data)
#
#     # 解析二级评论
#     def get_two_data(self, url, data):
#         response = requests.get(url, headers=self.headers, params=data)
#         if response.status_code == 200:
#             json_data = response.json()
#             two_name = jsonpath(json_data, '$..data..screen_name')  # 二级评论的作者
#             two_text = jsonpath(json_data, '$..data..text')  # 二级评论的作者
#             for two_names, two_texts in zip(two_name, two_text):
#                 comment = re.sub('<.*?>', '', two_texts)  # 评论 --> 正则处理html 字符
#                 print('\t', '----二级评论----')
#                 print('\t\t', two_names, comment)
#             # 开始二级评论翻页
#             two_max_id = jsonpath(json_data, '$..max_id')[0]  # 二级评论的翻页ID
#             print("二级评论的翻页ID:", two_max_id)
#             if two_max_id ==0:
#                 print('二级翻页结束~')
#                 # 二级翻页结束之后将max_id恢复为0 便于下一条一级评论翻页爬取
#                 self.two_data['max_id'] = 0
#             else:
#                 # time.sleep(random.randint(3, 7))
#                 self.two_data['max_id'] = two_max_id  # 切换二级评论翻页ID
#                 self.get_two_data(self.two_url, self.two_data)
#
#
#     def main(self):
#         self.get_one_data(self.one_url, self.one_data)
#         # self.get_two_data(self.two_url, self.two_data)
#
#
# if __name__ == '__main__':
#     weibo = WeiBo()
#     weibo.main()


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
import requests
from jsonpath import jsonpath
import time
import re
import sys
import time
import random


class WeiBo():
    def __init__(self):
        # 一级评论接口信息
        self.one_url = 'https://m.weibo.cn/comments/hotflow'
        self.one_data = {
            'id': '5100162104168525',
            'mid': '5100162104168525',
            'max_id_type': '0',
            'max_id': None  # 一级 翻页ID  （第一页无该参数 所以赋值为None）
        }
     # https://m.weibo.cn/detail/4864041232896092 测试
        # https://m.weibo.cn/detail/4865363672566456 测试
        # 二级评论接口信息
        self.two_url = 'https://m.weibo.cn/comments/hotFlowChild'
        self.two_data = {
            'cid': '4879471498232275',  # 跟评ID
            'max_id': '0',  # 翻页ID
            'max_id_type': '0'
        }
        self.headers = {
            # 'Referer': 'https://m.weibo.cn/detail/4864041232896092',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
            'cookie': 'SCF=AjPXgeTU4Ehy_2gArLcI-PHYuE91EzmYN6DqLM2cmBAHHQLd6rEwLmxVmDJ3_HDYWoC42UwZWcUEC0D-MeZl4I0.; SUB=_2A25KMECWDeRhGeFK7VIZ9CnNzDmIHXVpTNxerDV6PUJbktANLWXYkW1NQyQiyGsZIDd5JKBYkP1Mc7pop50bEp0k; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9W5q3UroJ_g71F4JEfCQHrkl5NHD95QNShq71hBNeKMfWs4DqcjMi--NiK.Xi-2Ri--ciKnRi-zNS0BcehnXS02NSBtt; SSOLoginState=1731473606; ALF=1734065606; _T_WM=12747584481; XSRF-TOKEN=2f5c9b; WEIBOCN_FROM=1110003030; MLOGIN=1; M_WEIBOCN_PARAMS=fid%3D100103type%253D1%2526q%253D%25E5%25A2%259E%25E5%258A%25A0%25E5%2581%2587%25E6%259C%259F%26uicode%3D10000011'
        }

    # 1，请求并解析一级评论
    def get_one_data(self, url, data):
        response = requests.get(url, headers=self.headers, params=data)
        print(response.status_code,response.text)
        if response.status_code == 200:
            json_data = response.json()
            print(json_data)
            one_name = jsonpath(json_data, '$..data[0:20].user.screen_name')  # 一级 作者
            one_text = jsonpath(json_data, '$..data[0:20].text')  # 一级 评论
            print("hhhh",one_name)
            print("hhhh",one_text)
            # if one_name == False:
            #     print('当前一级接口无数据~',response.url)
            #     # sys.exit('程序结束！')
            # 3.2 为了获取时知道二级评论来自哪条跟评 需要在一级评论接口中解析rootid（跟评ID）
            mid = jsonpath(json_data, '$..[0:20].rootid')  # 获取一级评论中的跟评ID

            for one_names, one_texts, mids in zip(one_name, one_text, mid):
                comment = re.sub('<.*?>', '', one_texts)  # 评论 --> 正则处理html 字符
                print('----一级评论----')
                print(one_names, '-->', comment)
                # print('==============')
                # 3.4 有些一级评论下无跟评 该异常需要捕捉
                try:
                    # 3.3 切换跟评ID 以此获得每条一级评论下的跟评
                    self.two_data['cid'] = mids
                    # 3.1 调用解析方法发现 二级评论重复打印
                    self.get_two_data(self.two_url, self.two_data)
                    t = random.randint(3,9)
                    time.sleep(t)
                except:
                    self.two_data['max_id'] = 0
                    print('当前一级评论已无跟评~ 将继续爬取后续一级评论')
            # 2，开始对一级评论翻页爬取
            # 2.1 经分析可得：翻页id在上一页接口数据中 健名为max_id
            max_id = jsonpath(json_data, '$..data.max_id')[0]  # 一级评论 翻页ID
            print("当前一级评论翻页ID：", max_id)
            if max_id == 0:
                sys.exit('该用户一级评论已爬取完~')
            else:
                # 更改翻页参数
                self.one_data['max_id'] = max_id
                # 2.2 递归调用自己 实现翻页爬取
                self.get_one_data(self.one_url, self.one_data)
                t = random.randint(4, 9)
                time.sleep(t)

    # 3，请求二级评论接口并解析二级评论内容
    def get_two_data(self, url, data):
        response = requests.get(url, headers=self.headers, params=data)
        if response.status_code == 200:
            json_data = response.json()
            two_name = jsonpath(json_data, '$..data..screen_name')  # 二级评论的作者
            two_text = jsonpath(json_data, '$..data..text')  # 二级评论的作者
            for two_names, two_texts in zip(two_name, two_text):
                comment = re.sub('<.*?>', '', two_texts)  # 评论 --> 正则处理html 字符
                print('\t\t', '----二级评论----')
                print('\t\t\t', two_names, comment)

            # 4，开始二级评论翻页
            two_max_id = jsonpath(json_data, '$..max_id')[0]  # 解析出翻页ID  健名为max_id
            print("~~~~~二级评论正在翻页，翻页ID:", two_max_id)
            # 4.2 因翻页总有翻完的时候，每当当前一级评论下的二级评论全部翻页完成 应当接着翻下一条一级评论的所有跟评
            # 当翻页结束max_id为0
            if two_max_id == 0:
                print('！！！！！二级翻页结束,ID为{}！！！！！！'.format(two_max_id))
                # 4.3 二级翻页结束之后将max_id恢复为0 便于下一条一级评论翻页爬取
                self.two_data['max_id'] = 0
            else:
                # 4.1 切换二级接口翻页参数 且递归调用自己实现二级翻页
                self.two_data['max_id'] = two_max_id
                self.get_two_data(self.two_url, self.two_data)
                t = random.randint(5, 9)
                time.sleep(t)

    def main(self):
        self.get_one_data(self.one_url, self.one_data)
        t = random.randint(5, 9)
        time.sleep(t)
        # self.get_two_data(self.two_url,self.two_data)


if __name__ == '__main__':
    s = WeiBo()
    s.main()
