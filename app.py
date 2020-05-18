#!/usr/bin/env ptyhon

import base64
import hashlib
import json
import os
import pickle
import sys
import urllib
import uuid

import numpy as np

import config
import redis
from flask import Flask, abort, jsonify, request

"""
Instantitate
"""
POOL = redis.ConnectionPool(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB,
            password=config.REDIS_AUTH_PASSWORD)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 20971520

@app.route('/enqueue/<path:url>', methods=['GET'])
def enqueue(url):
    #TODO: Add validation
    redis_conn = redis.Redis(connection_pool=POOL)
    image_id = hashlib.md5(url.encode('utf8')).hexdigest()

    cached_result = redis_conn.hget("{}::status".format(config.REDIS_NAMESPACE), image_id)
    print(cached_result)
    if cached_result == None:
        query = {
            "type" : "url",
            "image_id":image_id,
            "url":url
        }
        redis_conn.rpush(
            "{}::{}".format(
                config.REDIS_NAMESPACE, config.QUEUE_KEY),
            json.dumps(query))

        status = "AICROWD_SNAKES_API.IMAGE_ENQUEUED"
        _response = {
                    "image_id": image_id,
                    "status": status,
                    "response_channel": config.RESPONSE_CHANNEL,
                    "api_version":0.1
                }

        # Store processing status in a hash
        redis_conn.hset(
            "{}::status".format(config.REDIS_NAMESPACE),
            image_id,
            json.dumps(_response)
        )
        return jsonify(_response)
    else:
        # Push results into response channel for consistency
        redis_conn.rpush(config.RESPONSE_CHANNEL, cached_result)
        return jsonify(json.loads(cached_result))

@app.route('/enqueue_base64', methods=['POST'])
def enqueue_base64():
    redis_conn = redis.Redis(connection_pool=POOL)
    image_base64 = request.form.get('image_base64')
    query = {"type":"base64", "image_base64":image_base64}
    image_id = hashlib.md5(image_base64).hexdigest()
    query["image_id"] = image_id
    redis_conn.rpush("{}::{}".format(config.REDIS_NAMESPACE, config.QUEUE_KEY), json.dumps(query))
    status = "AICROWD_SNAKES_API.IMAGE_ENQUEUED"
    _response = {"image_id": image_id , "status":status, "response_channel":config.RESPONSE_CHANNEL, "api_version":0.1}
    redis_conn.hset("{}::status".format(config.REDIS_NAMESPACE), query["image_id"], json.dumps(_response))
    return jsonify(_response)


@app.route('/status/<path:image_id>', methods=['GET'])
def status(image_id):
    image_id = image_id.strip()
    redis_conn = redis.Redis(connection_pool=POOL)
    result = redis_conn.hget("{}::status".format(config.REDIS_NAMESPACE), image_id)
    if result == None:
        abort(404)
    else:
        return jsonify(json.loads(result))

app.run(host='0.0.0.0',port=3001 ,debug=config.DEBUG_MODE)
