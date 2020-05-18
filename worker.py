#!/usr/bin/env python

import base64
import json
import os
import sys
import urllib
import uuid

import numpy as np
import requests
from PIL import Image

import config
import redis

"""
Configurable Params
"""
N = 5 #Number of top predictions to respond back with

"""
Instantiate
"""

POOL = redis.ConnectionPool(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB,
            password=config.REDIS_AUTH_PASSWORD
        )

MODEL_DIRECTORY = "."
classes = open("{}/labels.txt".format(MODEL_DIRECTORY)).readlines()
classes = [x.strip() for x in classes]

def url_to_image(url):
    """
    Downloads and saves image from a url
    """
    filepath=os.path.join(
        "/tmp/",
        str(uuid.uuid4())+".jpg")
    image_data = requests.get(url).content
    f = open(filepath, "wb")
    f.write(image_data)
    f.close() 
    return filepath

def base64_to_image(image_base64):
    decoded_im = base64.b64decode(image_base64)
    filepath=os.path.join(
        "/tmp/",
        str(uuid.uuid4())+".jpg")
    f = open(filepath, "wb")
    f.write(decoded_im)
    f.close()
    return filepath


def predict(data, base64=False):
    if base64:
       img_path = base64_to_image(data)
    else:
       img_path = url_to_image(data)

    im = Image.open(img_path)
    predictions = [np.random.rand() for _ in classes]
    top_n = np.array(predictions).argsort()[::-1][:N]
    _labels = []
    _probs = []
    _labels = [classes[x] for x in top_n]
    _probs = [float(predictions[x]) for x in top_n]
    # Clean up image
    os.remove(img_path)
    return {"predictions" : _labels, "confidence":_probs}


print("Listening on ", "{}::{}".format(config.REDIS_NAMESPACE, config.QUEUE_KEY))
while True:
    redis_conn = redis.Redis(connection_pool=POOL)
    listen_key, _query = redis_conn.blpop("{}::{}".format(config.REDIS_NAMESPACE, config.QUEUE_KEY))
    _query = json.loads(_query)
    print("Received Query : ", _query["image_id"])
    _response = {}
    _response["api_version"] = 0.1
    _response["status"] = "AICROWD_SNAKES_API.IMAGE_PROCESSED"
    _response["image_id"] = _query["image_id"]
    try:
        if _query["type"] == "url":
            _result = predict(_query['url'])
            _response["result"] = _result
        elif _query["type"] == "base64":
            _result = predict(_query['image_base64'], base64=True)
            _response["result"] = _result
        else:
            raise Exception("Query Type not implemented. Please contact the Server administrators.")
    except Exception as e:
        _response["status"] = "AICROWD_SNAKES_API.ERROR_PROCESSING_IMAGE"
        _response["error_message"] = str(e)
    #Push result into response channel queue
    print(_response)
    redis_conn.rpush(config.RESPONSE_CHANNEL, json.dumps(_response))
    print("Response pushed to {}".format(config.RESPONSE_CHANNEL))
    # Store processing status in a hash
    redis_conn.hset("{}::status".format(config.REDIS_NAMESPACE), _response["image_id"], json.dumps(_response))
