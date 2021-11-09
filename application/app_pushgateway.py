# -*- coding: utf-8 -*-

import threading
import requests
import time
from tools import RedisHelper, RedisOperator, get_num_str
from configs import SUBSCRIBE_SERVER_CHANNEL, SUBSCRIBE_CLIENT_CHANNEL, DELIMER, HOST
import prometheus_client
from prometheus_client import Gauge
from prometheus_client.core import CollectorRegistry

threads = []
redis_op = RedisOperator("appname")
# 自定义指标必须利用CollectorRegistry进行注册，注册后返回给prometheus
# CollectorRegistry必须提供register，一个指标收集器可以注册多个collectoryregistry
REGISTRY = CollectorRegistry(auto_describe=False)
CLIENT_URL = "http://"+HOST+":9091/metrics/job/app/"
SERVER_URL = "http://"+HOST+":9091/metrics/job/server/"

# 创建指标(指标名称，指标注释信息，[]定义标签的类别及个数)
app_wbw = Gauge("app_wbw", "average write bandwidth of app in monitoring interval", ["appname"], registry=REGISTRY)
app_rbw = Gauge("app_rbw", "average read bandwidth of app in monitoring interval", ["appname"], registry=REGISTRY)
app_r_delay = Gauge("app_r_delay", "average read delay of app in monitoring interval", ["appname"], registry=REGISTRY)
app_w_delay = Gauge("app_w_delay", "average write delay of app in monitoring interval", ["appname"], registry=REGISTRY)
app_data_iops = Gauge("app_data_iops", "average data iops of app in monitoring interval", ["appname"], registry=REGISTRY)
app_create_iops = Gauge("app_create_iops", "average create iops of app in monitoring interval", ["appname"], registry=REGISTRY)
app_unlink_iops = Gauge("app_unlink_iops", "average unlink iops of app in monitoring interval", ["appname"], registry=REGISTRY)
app_stat_iops = Gauge("app_stat_iops", "average stat iops of app in monitoring interval", ["appname"], registry=REGISTRY)
app_open_iops = Gauge("app_open_iops", "average open iops of app in monitoring interval", ["appname"], registry=REGISTRY)
metricsdict = {"app_wbw":{}, "app_rbw":{}, "app_r_delay":{}, "app_w_delay":{}, "app_data_iops":{}, "app_create_iops":{}, "app_unlink_iops":{}, "app_stat_iops":{}, "app_open_iops":{}}
lock = threading.Lock()
class redisThread(threading.Thread):
    def __init__(self, name, channel, url):
        threading.Thread.__init__(self)
        self.name = name
        self.channel = channel
        self.url = url

    def run(self):
        print("redisThread is starting")
        obj = RedisHelper()
        redis_sub = obj.subscribe(self.channel)
        while True:
            msg = redis_sub.parse_response()
            # print("-----name:", self.name)
            update_result(msg, self.url)
            # print("%s: update_result %s" % (self.name, time.ctime(time.time())))
def addtodict3(thedict, key_a, key_b, key_c, val):
    if key_a in thedict:
        if key_b in thedict[key_a]:
            thedict[key_a][key_b].update({key_c:val})
        else:
            thedict[key_a].update({key_b:{key_c:val}})
    else:
        thedict.update({key_a:{key_b:{key_c:val}}})
def pushdata():
    global lock
    global metricsdict
    global CLIENT_URL
    redis_query = RedisOperator("appname")
    print("pushdataThread is starting")
    while True:
        time.sleep(1)
        lock.acquire(True)
        for metric in metricsdict:
            for appname in list(metricsdict[metric].keys()):
                if redis_query.ismember(redis_query.appname, appname):
                    eval(metric).labels(appname = appname).set(sum(metricsdict[metric][appname].values()))
                else:
                    metricsdict[metric].pop(appname)
        lock.release()
        requests.post(CLIENT_URL, data = prometheus_client.generate_latest(REGISTRY))
def update_result(msg, url):
    print("msg: ", msg)
    global redis_op
    global metricsdict
    global lock
    for index in range(len(msg)):
        msg[index] = str(msg[index], encoding="utf-8")
    msg = str(msg[2]).strip().split(DELIMER)
    print("msg = ", msg)
    # 字符串格式：  服务节点IP#client标识#时间戳#监控指标名#监控数值
    server = msg[0]
    appname = msg[1]
    print("appname = ",appname)
    metrics = []
    values = []
    for i in range(3, len(msg)):
        if i % 2 :
            metrics.append(msg[i])
            values.append(msg[i + 1])
    # 有应用运行时才上报指标
    if len(redis_op.get_all_app()) == 0:
        return

    # for i in range(len(metrics)):
    #    eval(metrics[i]).labels(appname=appname, serverip=server).set(values[i])
    lock.acquire(True)
    for i in range(len(metrics)):
        addtodict3(metricsdict, metrics[i], appname, server, float(values[i]))
    lock.release()
    # 向指定的API发送post信息，将注册的信息发过去
    # API中的 “python”是 job的名字
    # print(prometheus_client.generate_latest(REGISTRY))
    # requests.post(url, data=prometheus_client.generate_latest(REGISTRY))

if __name__ == "__main__":
    redis_client_thread = redisThread("redis-client", SUBSCRIBE_CLIENT_CHANNEL, CLIENT_URL)
    redis_server_thread = redisThread("redis-server", SUBSCRIBE_SERVER_CHANNEL, SERVER_URL)
    redis_client_thread.start()
    threads.append(redis_client_thread)
    redis_server_thread.start()
    threads.append(redis_server_thread)
    t_push = threading.Thread(target=pushdata)
    t_push.start()
    for t in threads:
        t.join()
    # 开启发送线程
    # t_push = threading.Thread(target=pushdata)
    # t_push.start()
    t_push.join()
