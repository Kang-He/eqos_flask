# -*- coding: utf-8 -*-

class monitor_info:
    def __init__(self, server_ip, app, timestamp, metric, value):
        self.server_ip = server_ip
        self.app = app
        self.timestamp = timestamp
        self.metric = metric
        self.value = value

    def get_server_ip(self):
        return self.server_ip

    def set_server_ip(self, server_ip):
        self.server_ip = server_ip

    def get_app(self):
        return self.app

    def set_app(self, app):
        self.app = app

    def get_timestamp(self):
        return self.timestamp

    def set_timestamp(self, timestamp):
        self.timestamp = timestamp

    def get_metric(self):
        return self.metric

    def set_metric(self, metric):
        self.metric = metric

    def get_value(self):
        return self.value

    def set_value(self, value):
        self.value = value

    def display(self):
        print("monitor_info: ", self.app, self.timestamp, self.metric, self.value)