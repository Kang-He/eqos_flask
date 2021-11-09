# -*- coding: utf-8 -*-

REDIS_DB_URL = {
    'host': '20.0.11.2',
    'port': 9809,
    'password': '',
    'db': 0
}

PUBLISH_CHANNEL = "qos"
PUBLISH_MONITOR_CHANNEL = "monitor"
SUBSCRIBE_SERVER_CHANNEL = "server"
SUBSCRIBE_CLIENT_CHANNEL = "client"
DELIMER = "^^"

set_keys = ['app_rbw', 'app_wbw', 'app_data_iops', 'app_create_iops', 'app_open_iops', 'app_unlink_iops', 'app_stat_iops']

keys = ['app_rbw', 'app_wbw', 'app_data_iops', 'app_create_iops', 'app_open_iops', 'app_unlink_iops', 'app_stat_iops'
        , 'app_w_delay', 'app_r_delay', 'app_name']

# 提供计算节点与存储节点的对应关系
fix=".7hdd.cloudincr-pg0.wisc.cloudlab.us"
server_list=['128.105.144.165', '128.105.144.151']
compute_dict = {'node-3'+fix: server_list,
                'node-4'+fix: server_list,
                'node-5'+fix: server_list}

HOST='20.0.11.2'
# HOST='0.0.0.0'
