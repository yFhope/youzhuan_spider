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

        # self.name = input('请输入你要检索的微博词汇:')
        self.name = '高椅岭'
        self.data = {
            'containerid': '100103type=1&q={}',
            'page_type': 'searchall',
            'page': None
        }
        self.data['containerid'] = self.data['containerid'].format(self.name)



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
                old_str = 'sinaweibo://selectchannel'
                new_str = 'https://m.weibo.cn/api/container/getIndex'
                self.navbar_name_url_item[name] = scheme.replace(old_str, new_str)

            # user_choice = input('请输入你想接入的接口(实时、用户、关注...):')
            # if user_choice == '实时':
            #     self.real_time_api()

    # 微博 实时板块 接口
    def real_time_api(self,page_number=1):
        page_args = f'&page_type=searchall&page={page_number}'
        url = self.navbar_name_url_item['实时'] + page_args
        while True:
            response = requests.get(url, headers=self.headers)
            page_number = 0
            if response.status_code == 200:
                json_data = response.json()
                user_names = jsonpath(json_data, '$..cards[:].mblog..screen_name')  # 发表微博的用户昵称
                genders = jsonpath(json_data, '$..cards[:].mblog..gender')  # 发表微博的用户性别 m-男 f-女
                followers_counts = jsonpath(json_data, '$..cards[:].mblog..followers_count')  # 用户粉丝数
                follow_counts = jsonpath(json_data, '$..cards[:].mblog..follow_count')  # 用户关注数 关注了多少人
                sources = jsonpath(json_data, '$..cards[:].mblog.source')  # 发表微博的设备信息

                comments_counts = jsonpath(json_data, '$..cards[:].mblog..comments_count')  # 微博的评论数
                attitudes_counts = jsonpath(json_data, '$..cards[:].mblog..attitudes_count')  # 微博的点赞数
                reposts_counts = jsonpath(json_data, '$..cards[:].mblog..reposts_count')  # 微博的转发数
                release_times = jsonpath(json_data, '$..cards[:].mblog..created_at')  # 发表微博的时间


                status_countrys = jsonpath(json_data, '$..cards[:].mblog..status_country')  # 用户IP所在国家
                status_provinces = jsonpath(json_data, '$..cards[:].mblog..status_province')  # 用户IP所在省
                # status_citys = jsonpath(json_data, '$..cards[:].mblog..status_city')  # 用户IP所在城市 - 不一定都有 舍弃

                weibo_texts = jsonpath(json_data, '$..cards[:].mblog.text')  # 微博正文内容
                textLengths = jsonpath(json_data, '$..cards[:].mblog.textLength')  # 正文文本长度

                # 跟进抓取评论信息用
                blog_ids = jsonpath(json_data, '$..cards[:].mblog.id')  # 发表微博 文章的ID
                # 获取翻页参数
                page_number = jsonpath(json_data, '$..cardlistInfo.page')[0]
                for text, name, bid in zip(weibo_texts,user_names,blog_ids):
                    # 二次处理文本信息，把标签全部去掉
                    new_text = re.sub('<.*?>', '', text)  # 微博正文

                    print(f'\033[1;35m{name}:  {new_text}\033[0m')  # 紫红色效果打印

                    # 获取一级评论
                    self.level1_data['id'] = bid
                    self.level1_data['mid'] = bid
                    self.level_1_comments()

            # 上一页的微博、评论获取完毕之后，开始翻页
            if page_number > 1:
                self.data['page'] = page_number
                time.sleep(random.uniform(1, 5))
                self.real_time_api(page_number)
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
                    print(f'\033[1;32m\t\t{new_name} --1--> {text}\033[0m')  # 绿色效果打印

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
                # print('一级翻页id:', self.max_id)
                self.level1_data['max_id'] = max_id
                if self.level1_data['max_id'] == 0:
                    print(f'\033[1;32m一级评论已全部获取完毕\033[0m')  # 绿色效果打印
                    break
                else:
                    # 1.3 递归调用，递归肯定会有程序报错的时候，所以我们要异常处理
                    time.sleep(random.uniform(3, 9))
                    self.level_1_comments()
        except:
            # print('\t\t========没有一级评论========')
            print(f'\033[1;31m\t\t========没有一级评论========\033[0m')  # 红色效果打印

    # 获取二级评论
    def level_2_comments(self):
        while True:
            second_response = requests.get(self.second_url, params=self.level2_data, headers=self.headers)
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
            self.level2_data['max_id'] = self.second_max_id
            # 2.3 max_id=0时翻页结束，不等于0才递归
            if self.level2_data['max_id'] in (0, 186494897570):  # 第一条评论的最后一条跟评的数据报的max_id不知道怎么会使变了，所以只能加进来，否则程序报错
                print('\t\t\t\t=========二级评论获取完毕=========')
                self.level2_data['max_id'] = 0
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
        self.get_navbar()
        self.real_time_api()


if __name__ == '__main__':
    weibo = WeiBo()
    weibo.main()
