from flask import Flask, request, render_template, jsonify, redirect, url_for, make_response
from flask_cors import CORS
from flask_restful import reqparse, abort, Api, Resource
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from tasks import *
# import worker_init
# from flask_rq2 import RQ
from redis import Redis
import rq
from rq.job import Job
import requests
from requests.exceptions import Timeout
import traceback
import json

from datetime import datetime
import random
import time

import pymongo
import os, ssl
# if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
#     getattr(ssl, '_create_unverified_context', None)):
#     ssl._create_default_https_context = ssl._create_unverified_contexts

client = pymongo.MongoClient("REDACTED", ssl_cert_reqs=ssl.CERT_NONE)
db = client.cached
fp = db.fp
places = db.places
users = db.users

import sentry_sdk
from sentry_sdk import capture_exception
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.rq import RqIntegration
from sentry_sdk.integrations.redis import RedisIntegration

sentry_sdk.init(
    dsn="REDACTED",
    integrations=[FlaskIntegration(), RqIntegration(), RedisIntegration()]
)

API_KEY = 'REDACTED'
BT_API = 'REDACTED'
DARKSKY_KEY = "REDACTED"

app = Flask(__name__)
CORS(app)
# rq = RQ(app)

redis = Redis.from_url('REDACTED')
queue = rq.Queue(connection=redis)
# worker = rq.Worker(queue, connection=redis)
# worker.work()

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["5 per minute", "1 per second"], # client facing
)

@app.route('/api/places/search', methods=['GET'])
def search():
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    radius = request.args.get('radius')
    keyword = request.args.get('keyword')
    category = request.args.get('type')

    if(not lat or not lng or not keyword):
        response = {
            "success": False,
            "error": "Missing arguments."
        }
        return jsonify(response)

    res = getNearbyPlaces(session, keyword, lat, lng, radius, category)

    response = {
        "success": True,
        "result": res
    }
    return jsonify(response)


@app.route('/api/popular_times', methods=['GET'])
@limiter.limit("5 per minute")
def pop_times():
    ua = request.headers.get('User-Agent')
    print(ua)
    address = request.args.get('address')
    timestamp = request.args.get('ts')
    if(not address):
        response = {
            "success": False,
            "error": "Missing arguments."
        }
        return jsonify(response)

    job = queue.enqueue(getPopularTimes, address, ua, None)
    return jsonify({
        "status":"queued",
        "job-id": job.get_id()
    })
    # session = refreshProxy(session)
    # lat and long here are for midpoint of search
    # places = getNearbyPlaces(session, keyword, lat, lng, radius, type)

@app.route('/api/popular_times/generic', methods=['GET'])
@limiter.limit("5 per minute")
def genericSearch():
    ua = request.headers.get('User-Agent')
    lat = request.args.get('lat') # opt
    lng = request.args.get('lng') # opt
    zipcode = request.args.get('zipcode')
    radius = request.args.get('radius')
    timestamp = request.args.get('ts')
    category = request.args.get('type')
    session = requests.session()
    if(not zipcode or not category):
        response = {
            "success": False,
            "error": "Missing arguments."
        }
        return jsonify(response)

    if not radius:
        radius = 5000

    if not lat or not lng:
        # need to find ourselves from zipcode
        lat_lng = getLatLng(session, zipcode)
        print(lat_lng)
        print(type(lat_lng))
        lat = lat_lng["lat"]
        lng = lat_lng["lng"]

    print("Getting nearby places")
    # EXPESIVE! but only way to filter by type i think
    places = getNearbyPlaces(session, "", lat, lng, radius, category)

    print(places)

    if(len(places) < 1):
        response = {
            "success": False,
            "error": "No results"
        }
        return jsonify(response)

    place_ids = []
    for p in places:
        place_ids.append(p["place_id"])

    closest = place_ids[0:2] # closest 3 places rn
    job_ids = []
    for place_id in closest:
        # getPopularTimes(None, ua, place_id)
        job = queue.enqueue(getPopularTimes, None, ua, place_id)
        job_ids.append(job.get_id())

    return jsonify({
        "status":"queued",
        "job-id": job_ids
    })

@app.route('/api/v2/live', methods=['GET'])
def liveForecast():
    name = request.args.get('name')
    address = request.args.get('address')
    if(not name or not address):
        response = {
            "success": False,
            "error": "Missing arguments."
        }
        return jsonify(response)

    session = requests.session()
    r = session.post('https://besttime.app/api/v1/forecasts/live?api_key_private={api_key}&venue_name={name}&venue_address={address}'.format(
        api_key=BT_API,
        name=name,
        address=address
    ))
    # print(r.text)

    res = json.loads(r.text)
    return jsonify(res)

@app.route('/api/v2/forecast', methods=['GET'])
def forecast():
    # venue_id = request.args.get('venue_id')
    name = request.args.get('name')
    address = request.args.get('address')
    if(not name or not address):
        response = {
            "success": False,
            "error": "Missing arguments."
        }
        return jsonify(response)

    url = "https://besttime.app/api/v1/forecasts"
    params = {
        'api_key_private': BT_API,
        'venue_name': name,
        'venue_address': address
    }

    session = requests.session()
    r = session.post(url, params=params)

    res = json.loads(r.text)
    # res.pop('api_key_private', None)
    return jsonify(res["venue_info"]);

@app.route('/api/status', methods=["GET"])
@limiter.limit("5 per second")
def status():
    id = request.args.get('id')
    try:
        job = Job.fetch(id, connection=redis)
    except Exception as ex:
        return jsonify({
            "status": "failed"
        })
    print('Status: %s' % job.get_status())
    response = {
        "status": "failed"
    }
    if(job.is_finished):
        response["status"] = "done"
        response["result"] = job.return_value
    elif job.is_queued:
        response["status"] = "queued"
    elif job.is_started:
        response["status"] = "waiting"
    elif job.is_failed:
        response["status"] = "failed"
    return jsonify(response)

@app.route('/test', methods=["GET"])
def test():
    response = {"success": True}
    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port="8080", ssl_context=('/etc/letsencrypt/live/app.uncrowd.me/fullchain.pem','/etc/letsencrypt/live/app.uncrowd.me/privkey.pem'))
