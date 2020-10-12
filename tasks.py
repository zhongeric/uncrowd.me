import requests
import json
import re
import traceback
from datetime import datetime
import urllib.parse
import binascii

API_KEY = 'REDACTED'

def refreshProxy(session):
    if len(PROXYLIST) != 0:
        prox = random.choice(PROXYLIST)
        proxi = {'https' : prox}
        session.proxies.update(proxi)
    return session

def getLatLng(session, zipcode):
    r = session.get("https://public.opendatasoft.com/api/records/1.0/search/?dataset=us-zip-code-latitude-and-longitude&q={zipcode}&rows=1".format(
        zipcode=zipcode
    ))
    json_loads = json.loads(r.text)
    lat_lng = {
        "lat": json_loads["records"][0]["fields"]["latitude"],
        "lng": json_loads["records"][0]["fields"]["longitude"]
    }
    return lat_lng

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
    # we don't request all bc billing costs , but we can always sadjust
    r = session.get("https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=formatted_address,formatted_phone_number,geometry/location,name,reference,website,url,utc_offset,icon,id,rating&key={api_key}".format(
        api_key=API_KEY,
        place_id=place_id
    ))
    json_loads = json.loads(r.text)
    return json_loads["result"]

def getNearbyPlaces(session, keyword, lat, lng, radius, category):
    print("https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&type={type}&keyword={keyword}&key={api_key}".format(
        api_key=API_KEY,
        lat=lat,
        lng=lng,
        radius=radius,
        type=category,
        keyword=keyword
    ))
    r = session.get("https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&type={type}&keyword={keyword}&key={api_key}".format(
        api_key=API_KEY,
        lat=lat,
        lng=lng,
        radius=radius,
        type=category,
        keyword=keyword
    ))

    json_loads = json.loads(r.text)
    print("Found {} places matching criteria".format(len(json_loads["results"])))
    return json_loads["results"]

def process_data(response):
    rr = str(response[4:])
    rr = rr.replace("null","None")

    # print(rr)

    e = eval(rr)
    # remove None
    # e = [i for i in e if i]
    m = e[6]
    enum_list = list(enumerate(m))

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
        try:
            for value in popular_times[0]:
                # 1 = Monday? 7 = Sunday
                if value[1] is not None:
                    for day in value[1]:
                        small_dict_popular_times[day[0]] = [day[1], day[2]]
                json_popular_times[value[0]] = small_dict_popular_times
        except Exception as ex:
            json_popular_times = None

    if hours_of_operations:
        try:
            for day in hours_of_operations[1]:
                #pp.pprint(day)
                if day[6]:
                    json_hours_of_operations[day[0]] = day[6]
                else:
                    json_hours_of_operations[day[0]] = day[1]
        except Exception as ex:
            json_hours_of_operations = None

    description = None
    if google_desc:
        # just take the first one
        try:
            description = google_desc[0][1]
        except Exception as ex:
            print(str(ex))
            description = None

    recommended = []
    if also_search_for:
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

    details = {}
    if more_details:
        try:
            store_type = more_details[0][0][1] # just get first
            # popular_for = more_details[0][2][2][0][1] # just get first one
            details["type"] = store_type
            # details["popular_for"] = popular_for
        except Exception as ex:
            details = None

    su = None
    if services_update:
        try:
            su = services_update[0][-1][0][0][0][2]
        except Exception as ex:
            pass

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
    return data

def getPopularTimes(address, ua, place_id=None):
    session = requests.session()
    if(place_id == None):
        place_id = getPlaceIdOnly(session, address)
    # place_id = getPlaceIdOnly(session, formatted_address)
    place_details = getPlaceDetails(session, place_id)
    print(place_details)
    # print(place_details)
    prog = re.compile('cid=(.+)')
    result = prog.search(place_details["url"])
    cid = result.groups()[0]

    lat = place_details["geometry"]["location"]["lat"]
    lng = place_details["geometry"]["location"]["lng"]
    name = place_details["name"]
    # time.sleep(20)

    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "referer": "https://www.google.com/",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": ua
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

    try:
        r = session.get(call_url, headers=headers, timeout=3)
    except Timeout as ex:
        print("Timeout")
        response = {
            "success": False,
            "error": "Could not fetch embed details - timed out"
        }
        return response
    if(r.status_code != 200):
        response = {
            "success": False,
            "error": "Could not fetch embed details - status code {}".format(r.status_code)
        }
        return response

    try:
        response = r.text
        data = process_data(response)
        data["geometry"] = {
            "lat": lat,
            "lng": lng
        }
        response = {
            "success": True,
            "data": data
        }
    except Exception as ex:
        print(str(ex))
        traceback.print_exc()
        response = {
            "success": False,
            "error": str(ex)
        }
    return response
