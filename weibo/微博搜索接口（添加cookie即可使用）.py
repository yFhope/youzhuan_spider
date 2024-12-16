import requests
import re
# import pymysql
import time
import random
from jsonpath import jsonpath


class WeiBo:
    def __init__(self):
        # 首页（搜索页）接口信息
        self.url = 'https://m.weibo.cn/api/container/getIndex'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1',
            'Referer': 'https://m.weibo.cn/detail/4813628149072458',
            'cookie': 'SCF=AhLNFup1PSAIQvfRs0LsF4ZWlu6OHeqhfP493lnPE6gpv90kJr6pdPq5ldui2vKI8mGzNhJVh3migfFLcjBgR1g.; _T_WM=11169871468; WEIBOCN_FROM=1110003030; MLOGIN=0; XSRF-TOKEN=21abca; M_WEIBOCN_PARAMS=luicode%3D10000011%26lfid%3D100103type%253D61%2526q%253D%25E9%25AB%2598%25E6%25A4%2585%25E5%25B2%25AD%2526t%253D%26fid%3D100103type%253D61%2526q%253D%25E9%25AB%2598%25E6%25A4%2585%25E5%25B2%25AD%2526t%253D%26uicode%3D10000011'
        }

        self.name = input('请输入你要检索的微博词汇:')
        self.data = {
            'containerid': '100103type=1&q={}',
            'page_type': 'searchall',
            'page': None
        }
        self.data['containerid'] = self.data['containerid'].format(self.name)

        # 一级评论的接口信息
        self.first_url = 'https://m.weibo.cn/comments/hotflow'
        self.first_data = {
            'id': '4813628149072458',
            'mid': '4813628149072458',
            'max_id': None,
            'max_id_type': '0'
        }

        # 二级评论的接口信息
        self.second_url = 'https://m.weibo.cn/comments/hotFlowChild'
        self.second_data = {
            'cid': '4813643344774141',
            'max_id': '0',
            'max_id_type': '0'
        }

        # # 数据库
        # self.db = pymysql.connect(host='localhost',  # 连接数据库
        #                           user='root',
        #                           passwd='zJ15679197024.',
        #                           database='toranto')
        # self.cursor = self.db.cursor()

    # 提取首页的所有关键名词、链接
    def get_first_data_api(self):
        response1 = requests.get(self.url, params=self.data, headers=self.headers)
        if response1.status_code == 200:
            self.get_first_data_json = response1.json()
            self.first_names = jsonpath(self.get_first_data_json, '$..channel_list[1:11]..name')
            self.first_schemess = jsonpath(self.get_first_data_json, '$..channel_list[1:11]..scheme')
            # 建立一个空字典对象
            first_scheme_dict = {}
            for self.first_name, self.first_schemes in zip(self.first_names, self.first_schemess):
                # 二次处理url信息，替换链接头
                self.first_scheme = self.first_schemes.replace('sinaweibo://selectchannel',
                                                               'https://m.weibo.cn/api/container/getIndex')
                print(self.first_name, end='\t')
                # print(self.first_name, self.first_scheme)
                # 将值添加入字典
                first_scheme_dict[self.first_name] = self.first_scheme

            # 选择界面
            print()
            first_choice = input('请输入你想接入的接口(实时、用户、关注...):')
            self.first_URL = first_scheme_dict[first_choice]
            # print(self.first_URL)
            if first_choice == '实时':
                self.real_time()

    # 根据get_first_data()方法获取到的first_URL进行分析检索，每个接口内容不同，所以需要构造不同的方法
    def real_time(self):
        while True:
            response2 = requests.get(self.first_URL, headers=self.headers)
            if response2.status_code == 200:
                self.get_shishi_data_json = response2.json()
                self.shishi_textss = jsonpath(self.get_shishi_data_json, '$..cards[:].mblog.text')  # 内容
                self.shishi_names = jsonpath(self.get_shishi_data_json, '$..cards[:].mblog..screen_name')  # 用户
                self.shishi_pinglun_ids = jsonpath(self.get_shishi_data_json, '$..cards[:].mblog.id')  # 每条微博对应的id
                # 获取翻页参数
                self.shishi_page = jsonpath(self.get_shishi_data_json, '$..cardlistInfo.page')[0]
                for self.shishi_texts, self.shishi_name, self.shishi_pinglun_id in zip(self.shishi_textss,
                                                                                       self.shishi_names,
                                                                                       self.shishi_pinglun_ids):
                    # 二次处理文本信息，把标签全部去掉
                    self.shishi_text = re.sub('<.*?>', '', self.shishi_texts)
                    # print(self.shishi_name, ':', self.shishi_text)
                    print(f'\033[1;35m{self.shishi_name}:  {self.shishi_text}\033[0m')  # 紫红色效果打印

                    # print('当前微博id为:', self.shishi_pinglun_id)
                    # 赋值id之后，​调用上一篇内容中获取评论的方法
                    self.first_data['id'] = self.shishi_pinglun_id
                    self.first_data['mid'] = self.shishi_pinglun_id
                    self.level1Comments()

            # 上一页的微博、评论获取完毕之后，开始翻页
            if self.shishi_page != 0:
                self.data['page'] = self.shishi_page
                time.sleep(random.uniform(1, 5))
            else:
                print('====实时动态已获取完毕====')  # 虽然不太可能运行到这里，但改写还是得写
                break  # 微博动态这么多，怎么可能爬的完，反正是个死循环。当然，主要是为了避免递归调用过多导致堆栈溢出


    # 获取level1Comments
    def level1Comments(self):
        try:  # 有可能没有一级评论，所以这次也要添加异常处理
            while True:
                self.first_response = requests.get(self.first_url, params=self.first_data, headers=self.headers)
                self.first_data_json = self.first_response.json()  # json数据类型
                # 根据网页数据包结构，获取以及评论的内容以及评论者
                self.first_names = jsonpath(self.first_data_json, '$..data[:].user.screen_name')
                self.first_textss = jsonpath(self.first_data_json, '$..data[:].text')
                # 3.2 获取一级评论的cid，以匹配二级评论。放入for循环中遍历
                self.cids = jsonpath(self.first_data_json, '$..data[:].rootid')
                for self.first_name, self.first_texts, self.cid in zip(self.first_names, self.first_textss, self.cids):
                    # print('=========一级评论=========')  # 分隔符
                    # print(f'\033[1;32m=========一级评论=========\033[0m')  # 绿色效果打印
                    self.first_text = re.sub('<.*?>', '', self.first_texts)  # 正则处理表情包
                    # print('\t\t', self.first_name, '--1-->', self.first_text)
                    print(f'\033[1;32m\t\t{self.first_name} --1--> {self.first_text}\033[0m')  # 绿色效果打印
                    # 3.3 将循环遍历得到的cid改写二级评论初始化字典值
                    self.second_data['cid'] = self.cid
                    # 3.1 调用二级评论方法
                    time.sleep(random.uniform(1, 7))
                    try:  # 异常处理：如果没有二级评论还调用二级方法，json()解析不到数据就会报错：requests.exceptions.JSONDecodeError
                        self.level2Comments()
                    except:
                        # print('\t\t\t--------没有二级评论--------')
                        print(f'\033[1;31m\t\t\t\t--------没有二级评论--------\033[0m')  # 效果红色打印
                        # ****************保存****************
                        # self.save_weibo_data('None', 'None')
                # 1.1获取网页max_id作为下一页的翻页参数
                self.max_id = jsonpath(self.first_data_json, '$..data.max_id')[0]
                # print('一级翻页id:', self.max_id)
                # 1.2 要等第一页爬完之后才能递归调用
                self.first_data['max_id'] = self.max_id
                # 2.4 根据2.4添加条件判断
                if self.first_data['max_id'] == 0:
                    # print('一级评论已全部获取完毕')
                    # print(f'\033[1;32m一级评论已全部获取完毕\033[0m')  # 绿色效果打印
                    break
                else:
                    # 1.3 递归调用，递归肯定会有程序报错的时候，所以我们要异常处理
                    time.sleep(random.uniform(3, 9))
        except:
            # print('\t\t========没有一级评论========')
            print(f'\033[1;31m\t\t========没有一级评论========\033[0m')  # 红色效果打印

    # 获取二级评论
    def level2Comments(self):
        while True:
            second_response = requests.get(self.second_url, params=self.second_data, headers=self.headers)
            self.second_data_json = second_response.json()  # json数据类型
            self.second_names = jsonpath(self.second_data_json, '$..data[:].user.screen_name')
            self.second_textss = jsonpath(self.second_data_json, '$..data[:].text')
            # print('\t\t\t\t', '-----------二级评论-----------')  # 分隔符
            for self.second_name, self.second_texts in zip(self.second_names, self.second_textss):
                self.second_text = re.sub('<.*?>', '', self.second_texts)  # 正则处理表情包
                print('\t\t\t\t', self.second_name, '--2-->', self.second_text)
                # 4 ****************保存****************
                # self.save_weibo_data(screen_name=shishi,second_name=self.second_name, second_text=self.second_text)
            # 2.1获取二级网页max_id作为下一页的翻页参数
            self.second_max_id = jsonpath(self.second_data_json, '$..max_id')[0]
            # print('\t\t二级翻页id:', self.second_max_id)
            # 2.2翻页参数替换
            self.second_data['max_id'] = self.second_max_id
            # 2.3 max_id=0时翻页结束，不等于0才递归
            if self.second_data['max_id'] in (0, 186494897570):  # 第一条评论的最后一条跟评的数据报的max_id不知道怎么会使变了，所以只能加进来，否则程序报错
                print('\t\t\t\t=========二级评论获取完毕=========')
                self.second_data['max_id'] = 0
                break
            else:
                time.sleep(random.uniform(2, 8))

    # 保存方法。有时候没有二级评论，如果保存方法只在二级评论方法中，①不仅导致二级评论解析时报错，②还会导致一级评论也无法保存
    # 什么时候需要单独保存一级评论？  --->  没有二级评论的时候，在异常处理中即可调用
    # 如果有二级评论，保存方法就放在二级评论解析中即可
    # def save_weibo_data(self, screen_name, weibo, first_name, first_text, second_name, second_text):
    #     sql = "insert into weibo_all(用户, 微博, 一级评论者, 一级评论, 二级评论者, 二级评论) values(%s, %s, %s, %s, %s)"  # 占位符
    #     data = [screen_name, weibo, first_name, first_text, second_name, second_text]  # 使用占位符插入数据，之前所有的代码前加self就是为了方便在类中共用变量，方便保存
    #     self.cursor.execute(sql, data)  # data要tuple、list、dict类型
    #     self.db.commit()

    def main(self):
        self.get_first_data_api()


if __name__ == '__main__':
    weibo = WeiBo()
    weibo.main()
