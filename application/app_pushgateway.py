# -*- coding: utf-8 -*-

import threading
import requests

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
app_wbw = Gauge("app_wbw", "average write bandwidth of app in monitoring interval", ["appname", "clientname", "serverip"], registry=REGISTRY)
app_rbw = Gauge("app_rbw", "average read bandwidth of app in monitoring interval", ["appname", "clientname", "serverip"], registry=REGISTRY)
app_r_delay = Gauge("app_r_delay", "average read delay of app in monitoring interval", ["appname", "clientname", "serverip"], registry=REGISTRY)
app_w_delay = Gauge("app_w_delay", "average write delay of app in monitoring interval", ["appname", "clientname", "serverip"], registry=REGISTRY)
app_data_iops = Gauge("app_data_iops", "average data iops of app in monitoring interval", ["appname", "clientname", "serverip"], registry=REGISTRY)
app_create_iops = Gauge("app_create_iops", "average create iops of app in monitoring interval", ["appname", "clientname", "serverip"], registry=REGISTRY)
app_unlink_iops = Gauge("app_unlink_iops", "average unlink iops of app in monitoring interval", ["appname", "clientname", "serverip"], registry=REGISTRY)
app_stat_iops = Gauge("app_stat_iops", "average stat iops of app in monitoring interval", ["appname", "clientname", "serverip"], registry=REGISTRY)
app_open_iops = Gauge("app_open_iops", "average open iops of app in monitoring interval", ["appname", "clientname", "serverip"], registry=REGISTRY)

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
            print("-----name:", self.name)
            update_result(msg, self.url)
            #print("%s: update_result %s" % (self.name, time.ctime(time.time())))

def update_result(msg, url):
    #print("msg: ", msg)
    global redis_op
    for index in range(len(msg)):
        msg[index] = str(msg[index], encoding="utf-8")
    msg = str(msg[2]).strip().split(DELIMER)
    print("msg = ", msg)
    # 字符串格式：  服务节点IP#client标识#时间戳#监控指标名#监控数值
    server = msg[0]
    client = msg[1]
    metrics = []
    values = []
    for i in range(3, len(msg)):
        if i % 2 :
            metrics.append(msg[i])
            values.append(msg[i + 1])
    # 有应用运行时才上报指标
    if len(redis_op.get_all_app()) == 0:
        return
    
    app_name = redis_op.get_app(client)
    if app_name == "":
        print("error: no appname.")
        return

    for i in range(len(metrics)):
        eval(metrics[i]).labels(appname=app_name, clientname=client, serverip=server).set(values[i])

    # 向指定的API发送post信息，将注册的信息发过去
    # API中的 “python”是 job的名字
    # print(prometheus_client.generate_latest(REGISTRY))
    requests.post(url, data=prometheus_client.generate_latest(REGISTRY))

if __name__ == "__main__":
    redis_client_thread = redisThread("redis-client", SUBSCRIBE_CLIENT_CHANNEL, CLIENT_URL)
    redis_server_thread = redisThread("redis-server", SUBSCRIBE_SERVER_CHANNEL, SERVER_URL)
    redis_client_thread.start()
    redis_client_thread.run()
    threads.append(redis_client_thread)
    redis_server_thread.start()
    redis_server_thread.run()
    threads.append(redis_server_thread)
    for t in threads:
        t.join()