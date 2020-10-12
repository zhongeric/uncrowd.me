from redis import Redis
import rq
import pymongo
import time
import os, ssl

client = pymongo.MongoClient("REDACTED", ssl_cert_reqs=ssl.CERT_NONE)
db = client.main
errors = db.workerErrors

def db_handler(job, exc_type, exc_value, traceback):
    # errors
    print(job, exc_type, exc_value, traceback)

redis = Redis.from_url('REDACTED')
queue = rq.Queue(connection=redis)
worker = rq.Worker(queue, connection=redis, exception_handlers=[db_handler])

worker.work()
