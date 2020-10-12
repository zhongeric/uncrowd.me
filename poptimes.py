import pprint
import time
from datetime import datetime
import random
pp = pprint.PrettyPrinter(indent=4)

import urllib.parse
import urllib.request
import requests
import ast
import re
import json
import time
import binascii

API_KEY = 'REDACTED'
BT_API = 'REDACTED'

def refreshProxy(session):
    if len(PROXYLIST) != 0:
        prox = random.choice(PROXYLIST)
        proxi = {'https' : prox}
        session.proxies.update(proxi)
    else:
        prox = ""
    return session

def getPlaceIdOnly(session, address):
    r = session.get("https://maps.googleapis.com/maps/api/place/findplacefromtext/json?key={api_key}&input={address}&inputtype=textquery&fields=place_id,name".format(
        api_key=API_KEY,
        address=address
    ))
    json_loads = json.loads(r.text)
    print("Place ID Found: ", json_loads["candidates"][0]["place_id"])
    print("Name Found ", json_loads["candidates"][0]["name"])
    return json_loads["candidates"][0]["place_id"]

def getPlaceDetails(session, place_id):
    # we don't request all bc billing costs , but we can always adjust
    r = session.get("https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=formatted_address,formatted_phone_number,geometry/location,name,reference,website,url,utc_offset,icon,id,rating&key={api_key}".format(
        api_key=API_KEY,
        place_id=place_id
    ))
    json_loads = json.loads(r.text)
    return json_loads["result"]

def getNearbyPlaces(session, keyword, lat, lng, radius, type=None):
    r = session.get("https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&type={type}&keyword={keyword}&key={api_key}".format(
        api_key=API_KEY,
        lat=lat,
        lng=lng,
        radius=radius,
        type=type,
        keyword=keyword
    ))

    json_loads = json.loads(r.text)
    print("Found {} places matching criteria".format(len(json_loads["results"])))
    return json_loads["results"]

def main():
    session = requests.session()
    # session = refreshProxy(session)

    # lat and long here are for midpoint of search
    # valid types:
    #   restuarant
    #   grocery_or_supermarket
    #   park

    places = getNearbyPlaces(session, "", 42.6068788, -83.11096549, 5000, None)
    pp.pprint(places)
    time.sleep(10)

    place_id = places[0]["place_id"]

    # place_id = getPlaceIdOnly(session, formatted_address)
    place_details = getPlaceDetails(session, place_id)

    print(place_details)

    prog = re.compile('cid=(.+)')
    result = prog.search(place_details["url"])
    cid = result.groups()[0]

    lat = place_details["geometry"]["location"]["lat"]
    lng = place_details["geometry"]["location"]["lng"]
    name = place_details["name"]
    # time.sleep(20)

    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US,en;q=0.9",
        "sec-fetch-site": "same-origin",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36"
    }

    startTime = datetime.now()

    #pb = "!1m14!1s0x8824c384d4484e2d%3A0x6a3990c40ec9aef0!3m9!1m3!1d10617.375549336732!2d-83.136659!3d42.5898522!2m0!3m2!1i662!2i694!4f13.1!4m2!3d42.589484623315535!4d-83.12977373600005!13m50!2m2!1i408!2i240!3m2!2i10!5b1!7m42!1m3!1e1!2b0!3e3!1m3!1e2!2b1!3e2!1m3!1e2!2b0!3e3!1m3!1e3!2b0!3e3!1m3!1e8!2b0!3e3!1m3!1e3!2b1!3e2!1m3!1e9!2b1!3e2!1m3!1e10!2b0!3e3!1m3!1e10!2b1!3e2!1m3!1e10!2b0!3e4!2b1!4b1!9b0!14m4!1sVq2tXqDcBN6u0PEP6_SXwAI!3b1!7e81!15i10555!15m39!1m4!4e2!18m2!3b0!6b0!2b1!4b1!5m5!2b1!3b1!5b1!6b1!7b1!10m1!8e3!14m1!3b1!17b1!20m2!1e3!1e6!24b1!25b1!26b1!30m1!2b1!36b1!43b1!52b1!55b1!56m2!1b1!3b1!65m5!3m4!1m3!1m2!1i224!2i298!22m1!1e81!29m0!30m1!3b1"

    # 0x0 %3A CID <- how to find cid? , removed Vq2tXqDcBN6u0PEP6_SXwAI <- idk what tf this is
    pb = "!1m14!1s0x0%3A{cid}!3m9!1m3!1d10617.375549336732!2d{lng}!3d{lat}!2m0!3m2!1i662!2i694!4f13.1!4m2!3d{lat}!4d{lng}!13m50!2m2!1i408!2i240!3m2!2i10!5b1!7m42!1m3!1e1!2b0!3e3!1m3!1e2!2b1!3e2!1m3!1e2!2b0!3e3!1m3!1e3!2b0!3e3!1m3!1e8!2b0!3e3!1m3!1e3!2b1!3e2!1m3!1e9!2b1!3e2!1m3!1e10!2b0!3e3!1m3!1e10!2b1!3e2!1m3!1e10!2b0!3e4!2b1!4b1!9b0!14m4!1s!3b1!7e81!15i10555!15m39!1m4!4e2!18m2!3b0!6b0!2b1!4b1!5m5!2b1!3b1!5b1!6b1!7b1!10m1!8e3!14m1!3b1!17b1!20m2!1e3!1e6!24b1!25b1!26b1!30m1!2b1!36b1!43b1!52b1!55b1!56m2!1b1!3b1!65m5!3m4!1m3!1m2!1i224!2i298!22m1!1e81!29m0!30m1!3b1".format(
        cid=hex(int(cid)),
        lat=lat,
        lng=lng
    )

    call_url = "https://www.google.com/maps/preview/place?authuser=0&hl=en&gl=us&pb={pb}&q={q}&pf=t".format(
        pb = pb,
        q = urllib.parse.quote(name)
    )

    # print(call_url)
    r = session.get(call_url)
    #print(r.url)
    response = r.text

    rr = str(response[4:])
    rr = rr.replace("null","None")

    e = eval(rr)
    # remove None
    # e = [i for i in e if i]
    m = e[6]
    enum_list = list(enumerate(m))

    # pp.pprint(enum_list)

    tfid = enum_list[10][-1]
    classifications = enum_list[13][-1]
    name_address = enum_list[18][-1]
    google_desc = enum_list[32][-1]
    hours_of_operations = enum_list[34][-1] # more nestinng to do
    tags = enum_list[76][-1]
    popular_times = enum_list[84][-1]
    also_search_for = enum_list[99][-1]
    more_details = enum_list[100][-1] # delivery, accessibility, etc.
    wait_spent_time = enum_list[117][-1]
    delivery_carryout = enum_list[122][-1] #uber eats, etc.
    services_update = enum_list[132][-1]
    logo_url = enum_list[157][-1]

    # pp.pprint([tfid, classifications, name_address, google_desc, hours_of_operations, tags, popular_times, also_search_for, more_details, wait_spent_time, delivery_carryout, services_update, logo_url])

    json_popular_times = {}
    small_dict_popular_times = {}
    json_hours_of_operations = {}

    if popular_times:
        for value in popular_times[0]:
            # 1 = Monday? 7 = Sunday
            if value[1] is not None:
                for day in value[1]:
                    small_dict_popular_times[day[0]] = [day[1], day[2]]
            json_popular_times[value[0]] = small_dict_popular_times

    if hours_of_operations:
        try:
            for day in hours_of_operations[1]:
                #pp.pprint(day)
                if day[6]:
                    json_hours_of_operations[day[0]] = day[6]
                else:
                    json_hours_of_operations[day[0]] = day[1]
        except:
            pass

    if google_desc:
        # just take the first one
        description = google_desc[0][1]

    if also_search_for:
        recommended = []
        for listing in also_search_for[0][0][1]:
            small = {}
            try:
                if(len(listing) > 1):
                    data = listing[1]
                    small["place_id"] = data[0]
                    small["rating"] = data[4][7]
                    small["review_cnt"] = data[4][8]
                    small["geo"] = {
                            "lat": data[9][-2],
                            "lng": data[9][-1]
                    }
                    small["tfid"] = data[10]
                    small["name"] = data[11]
                    # pp.pprint(small)
                    recommended.append(small)
            except Exception as ex:
                # print(str(ex))
                pass

    if more_details:
        details = {}
        store_type = more_details[0][0][1] # just get first
        # popular_for = more_details[0][2][2][0][1] # just get first one
        details["type"] = store_type
        # details["popular_for"] = popular_for

    if services_update:
        try:
            su = services_update[0][-1][0][0][0][2]
        except Exception as ex:
            su = ""

    data = {
        "tfid": tfid,
        "classifications": classifications,
        "name_address": name_address,
        "description": description,
        "hours_of_operation": json_hours_of_operations,
        "tags": tags,
        "popular_times": json_popular_times,
        "recommended": recommended,
        "more_details": details,
        "wait_time": wait_spent_time,
        "delivery_carryout": delivery_carryout,
        "su":su,
        "logo":logo_url
    }

    # pp.pprint(data)
    return data

def liveForecast():
    session = requests.session()
    r = session.post('https://besttime.app/api/v1/forecast/live?api_key_private={api_key}&venue_name={name}&venue_address={address}'.format(
        api_key=BT_API,
        name="McDonald's",
        address='2000 18 Mile Rd, Sterling Heights, MI 48310 United States'
    ))
    print(r.text)

    res = json.loads(r.text)

def scrapeType():
    '''https://www.google.com/search?tbm=map&authuser=0&hl=en&gl=us&pb=!4m12!1m3!1d10617.583616045282!2d-83.11127895!3d42.588630699999996!2m3!1f0!2f0!3f0!3m2!1i823!2i694!4f13.1!7i20!10b1!12m8!1m1!18b1!2m3!5m1!6e2!20e3!10b1!16b1!19m4!2m3!1i360!2i120!4i8!20m57!2m2!1i203!2i100!3m2!2i4!5b1!6m6!1m2!1i86!2i86!1m2!1i408!2i240!7m42!1m3!1e1!2b0!3e3!1m3!1e2!2b1!3e2!1m3!1e2!2b0!3e3!1m3!1e3!2b0!3e3!1m3!1e8!2b0!3e3!1m3!1e3!2b1!3e2!1m3!1e9!2b1!3e2!1m3!1e10!2b0!3e3!1m3!1e10!2b1!3e2!1m3!1e10!2b0!3e4!2b1!4b1!9b0!22m5!1sLkq7XvOqFcqGtQa4_pigBQ!4m1!2i5361!7e81!12e3!24m48!1m12!13m6!2b1!3b1!4b1!6i1!8b1!9b1!18m4!3b1!4b1!5b1!6b1!2b1!5m5!2b1!3b1!5b1!6b1!7b1!10m1!8e3!14m1!3b1!17b1!20m2!1e3!1e6!24b1!25b1!26b1!30m1!2b1!36b1!43b1!52b1!54m1!1b1!55b1!56m2!1b1!3b1!65m5!3m4!1m3!1m2!1i224!2i298!26m4!2m3!1i80!2i92!4i8!30m28!1m6!1m2!1i0!2i0!2m2!1i458!2i694!1m6!1m2!1i773!2i0!2m2!1i823!2i694!1m6!1m2!1i0!2i0!2m2!1i823!2i20!1m6!1m2!1i0!2i674!2m2!1i823!2i694!34m13!2b1!3b1!4b1!6b1!8m3!1b1!3b1!4b1!9b1!12b1!14b1!20b1!23b1!37m1!1e81!42b1!47m0!49m1!3b1!50m4!2e2!3m2!1b1!3b0!65m0&q=grocery%20stores&nfpr=1&tch=1&ech=1&psi=HUq7XoPOKoq3tQbW2LeoAQ.1589332510750.1'''


if __name__ == '__main__':
    # main()
    liveForecast()
