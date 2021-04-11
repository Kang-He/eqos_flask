# -*- coding: utf-8 -*-

import redis
from configs import REDIS_DB_URL

class RedisHelper:
    def __init__(self):
        self._conn = redis.Redis(**REDIS_DB_URL)

    # 发布消息
    def publish(self, channel, msg):
        self._conn.publish(channel, msg)
        return "success"

    # 订阅消息
    def subscribe(self, channel):
        pub = self._conn.pubsub()
        pub.subscribe(channel)
        pub.parse_response()
        return pub

class RedisOperator:
    def __init__(self, app):
        self._conn = redis.Redis(**REDIS_DB_URL)
        self.appname = app

    # 添加元素
    def add_dict(self, name, *values):
        self._conn.sadd(name, *values)
        self._conn.sadd(self.appname, name)
        for value in values:
            self._conn.set(value, name)

    # 删除元素
    def remove_dict(self, name):
        values = self._conn.smembers(name)
        self._conn.srem(self.appname, name)
        for value in values:
            self._conn.delete(value)
        self._conn.delete(name)

    # 获取所有元素
    def get(self, name):
        results = []
        for v in self._conn.smembers(name):
            results.append(str(v, encoding="utf-8"))
        return results

    # 是否含元素
    def ismember(self, name, value):
        return self._conn.sismember(name, value)

    # 获取元素个数
    def count(self, name):
        return self._conn.scard(name)

    # 获取app
    def get_app(self, value):
        if self._conn.get(value) != None:
            return str(self._conn.get(value), encoding="utf-8")
        else:
            return ""

    # 获取所有appname
    def get_all_app(self):
        results = []
        for app in self._conn.smembers(self.appname):
            results.append(str(app, encoding="utf-8"))
        return results

def get_num_str(s):
    s = filter(lambda ch: ch in '0123456789.', s)
    s = list(s)
    s = "".join(s)
    return s