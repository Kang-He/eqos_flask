# -*- coding: utf-8 -*-


from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS
from tools import RedisHelper, RedisOperator
from configs import PUBLISH_CHANNEL, PUBLISH_MONITOR_CHANNEL, DELIMER, keys, set_keys, HOST, compute_dict
import time

redis_op = RedisOperator("appname")

app = Flask(__name__)

# variables /search target:app_name
def app_name():
    global redis_op
    return redis_op.get_all_app()

@app.route('/')
def index():
    return jsonify({"code": 200, "message": "OK", "data": {}})

@app.route('/search', methods=['POST'])
def search():
    # print("request=", request.get_json())
    if "app_name" in request.get_json()['target']:
        return jsonify(app_name())
    elif "hotapp" in request.get_json()['target']:
        global redis_op
        return jsonify(redis_op.get_hotappname())
    else:
        query_list = ["app_num"]
        return jsonify(query_list)

# TODO: why no print?
@app.route('/query', methods=['POST'])
def query():
    # print("request=", request.get_json())
    for target in request.get_json()['targets']:
        data = []
        if "app_num" == target['target']:
            result = {}
            result["datapoints"] = [[len(app_name()), int(time.time() * 1000)]]
            result["target"] = "app_num"
            data.append(result)
            return jsonify(data)
    return jsonify({"code": 200, "message": "OK", "data": {}})

@app.route('/set_bw', methods=['POST'])
def set_bw():
    request_json = request.get_json()
    data = request_json['data']
    global redis_op
    obj = RedisHelper()
    message = "set_bw^^" + data
    obj.publish(PUBLISH_CHANNEL, message)
    return jsonify({"code": 200, "message": "OK", "data": {}})

@app.route('/exp_bw', methods=['POST'])
def exp():
    start = time.time() * 1000
    request_json = request.get_json()
    # print("/exp request_json: ", request_json, "\n")
    data = request_json['data']
    data = data.strip().split(':')
    tmp = {}
    for k in set_keys:
        tmp[k] = -1
    app_name = ""
    if data != "":
        app_name = data[0]
        for i in range(len(data)):
            if i == len(data) - 1:
                break
            elif i % 2 == 1:
                tmp[data[i]] = data[i + 1]
    # print("data: ",data)
    # print("tmp: ",tmp)
    # publish message
    global redis_op
    clients = redis_op.get(app_name)  # app_name??????client??????
    n = len(clients)
    obj = RedisHelper()
    for client in clients:
        # ????????????message
        message = client
        for (k, v) in tmp.items():
            # print("k: ", k, type(k), " v: ",v, type(v))
            if type(v) is str:
                v = float(v)
                message += DELIMER + k + DELIMER + str(v/n)  # ??????????????????compute
            else:
                message += DELIMER + k + DELIMER + str(v)
        obj.publish(PUBLISH_CHANNEL, message)
        print("publish", PUBLISH_CHANNEL, ": ", message)
    end = time.time() * 1000
    # print("set info consume: ", int(end - start), "ms")
    return jsonify({"code": 200, "message": "OK", "data": {}})


@app.route('/add_app', methods=['POST'])
def add_app():
    request_json = request.get_json()
    appname = request_json['data']['appname']
    computes = request_json['data']['computes']
    computes = computes.strip().split(DELIMER)
    global redis_op
    redis_op.add_dict(appname, *computes)
    redis_op.add_hotapp(appname)
    obj = RedisHelper()
    message = "app_nodes:" + DELIMER + appname
    for client in computes:
        message += DELIMER + client
    obj.publish(PUBLISH_MONITOR_CHANNEL, message)
    print("publish", PUBLISH_CHANNEL, ": ", message)
    return jsonify({"code": 200, "message": "OK", "data": {appname:computes}})


@app.route('/remove_app', methods=['POST'])
def remove_app() :
    global redis_op
    request_json = request.get_json()
    appname = request_json['data']['appname']
    clients = redis_op.get(appname)  # app_name??????client??????
    obj = RedisHelper()
    message = "remove_app:"
    for client in clients :
        message += DELIMER + client
    obj.publish(PUBLISH_CHANNEL, message) #????????????????????????????????????
    obj.publish(PUBLISH_MONITOR_CHANNEL, message)
    print("publish", PUBLISH_CHANNEL, ": ", message)
    print("publish", PUBLISH_MONITOR_CHANNEL, ": ", message)
    redis_op.remove_dict(appname) #??????redis??????????????????
    return jsonify({ "code": 200, "message" : "OK", "data" : appname })


@app.route('/relation', methods=['POST'])
def relation():
    global redis_op
    data = [{"name":"IO??????", "children":[]}]
    #print("compute_dict:", compute_dict)
    apps = redis_op.get_all_app()
    if len(apps) == 0:
        data[0]["name"] = "None"
    else:
        for app in apps:
            app_dict = {"name": app, "children": []}
            # ???????????????????????????
            for compute in redis_op.get(app):
                c_dict = {"name": compute, "children": []}
                # ???????????????????????????
                print("compute: ", compute)
                print(compute_dict[compute])
                for server in compute_dict[compute]:
                    s_dict = {"name": server}
                    c_dict["children"].append(s_dict)
                app_dict["children"].append(c_dict)
            data[0]["children"].append(app_dict)

    return jsonify({"code": 200, "message": "OK", "data": data})

@app.route('/map/<int:interval>', methods=['GET'])
def map(interval):
    return render_template('tree.html', interval=interval)

@app.route('/downloads/<filename>')
def downloads(filename):
    return send_from_directory(r"/root/monitor/eqos_flask/application/templates", filename, as_attachment = True)


if __name__ == "__main__":
    # flask backend start
    CORS(app, supports_credentials=True)
    app.run(host=HOST)
