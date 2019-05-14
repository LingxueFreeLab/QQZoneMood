import sys
import os
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(os.path.split(rootPath)[0])
from src.analysis.QQZoneAnalysis import QQZoneAnalysis
from src.spider.QQZoneSpider import QQZoneSpider
from src.util.constant import WEB_SPIDER_INFO, MOOD_NUM_PRE, CLEAN_DATA_KEY, GET_MAIN_PAGE_FAILED, LOGIN_FAILED, \
    USER_MAP_KEY, GET_MOOD_FAILED, MOOD_FINISH_KEY
import threading

# 获取空间动态数据
def capture_data():
    sp = QQZoneSpider(use_redis=True, debug=True, mood_begin=0, mood_num=-1,
                      stop_time='-1',
                      download_small_image=False, download_big_image=False,
                      download_mood_detail=True, download_like_detail=True,
                      download_like_names=True, recover=False, cookie_text=None)
    sp.login()
    sp.get_main_page_info()
    sp.get_mood_list()
    sp.user_info.save_user(sp.username)


# 提供给web的接口
def web_interface(username, nickname, stop_time, mood_num, cookie_text, no_delete, password, pool_flag):
    sp = QQZoneAnalysis(use_redis=True, debug=False, username=username, analysis_friend=True, from_web=True,
                        nickname=nickname, stop_time=stop_time, mood_num=mood_num, no_delete=no_delete, cookie_text=cookie_text, pool_flag=pool_flag)
    try:
        sp.login()
        sp.re.rpush(WEB_SPIDER_INFO + username, "用户" + str(sp.username) + "登陆成功")
        # 存储用户密码
        sp.re.hset(USER_MAP_KEY, username, password)
    except BaseException:
        sp.re.rpush(WEB_SPIDER_INFO + username, GET_MAIN_PAGE_FAILED)
    try:
        sp.get_main_page_info()
        sp.re.rpush(WEB_SPIDER_INFO + username, "获取主页信息成功")
        sp.re.rpush(WEB_SPIDER_INFO + username, MOOD_NUM_PRE + ":" + str(sp.mood_num))
    except BaseException:
        sp.re.rpush(WEB_SPIDER_INFO + username, LOGIN_FAILED)

    try:

        # 获取动态的数据
        t1 = threading.Thread(target=sp.get_mood_list)
        # 获取好友数据
        t2 = threading.Thread(target=sp.get_friend_detail)
        t1.setDaemon(False)
        t2.setDaemon(False)
        t1.start()
        t2.start()
        # 等待两个线程都结束
        t1.join()
        t2.join()
        # sp.user_info.save_user(username)
    except BaseException:
        sp.re.rpush(WEB_SPIDER_INFO + username, GET_MOOD_FAILED)
        exit(1)

    # 清洗好友数据
    sp.clean_friend_data()
    # 获取第一位好友数据
    sp.get_first_friend_info()
    # 清洗说说数据并计算点赞最多的人和评论最多的人
    sp.get_most_people()
    sp.calculate_send_time()
    sp.user_info.save_user()
    # 保存说说数据
    sp.export_mood_df()
    sp.re.set(MOOD_FINISH_KEY + str(username), 1)
    sp.calculate_history_like_agree()
    sp.re.set(CLEAN_DATA_KEY + username, 1)



def get_user_basic_info():
    sp = QQZoneSpider(use_redis=True, debug=False, mood_begin=0, mood_num=-1,
                      stop_time='2015-06-01',
                      download_small_image=False, download_big_image=False,
                      download_mood_detail=True, download_like_detail=True,
                      download_like_names=True, recover=False, cookie_text=None)

    return sp.user_info


def array_test():
    step = 1102 // 4
    for i in range(0, 4):
        print(i * step)


def test_step():
    sp = QQZoneSpider(use_redis=True, debug=True, mood_begin=0, mood_num=1000,
                      stop_time='-1',
                      download_small_image=False, download_big_image=False,
                      download_mood_detail=True, download_like_detail=True,
                      download_like_names=True, recover=False, cookie_text=None)
    sp.find_best_step(1100, 5)
    sp.find_best_step(1222, 5)
    sp.find_best_step(2222, 10)


if __name__ == '__main__':
    capture_data()
    # test_step()
