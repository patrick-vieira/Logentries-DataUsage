import asyncio
import os
import argparse

import grequests
import requests
import time
import datetime
import csv
import six
from aiohttp import ClientSession, web

from logentriesAPI.model import logset
from commons import humanizer, async_req

LOGENTRIES_API_URL = 'https://api.logentries.com'
LOGENTRIES_REST_URL = 'https://rest.logentries.com/query/logs/'
SEARCH_QUERY = "where(/.*/) calculate(bytes)"
# ACCOUNT_KEY = ""
# API_KEY = ""
TO_TS = ""
FROM_TS = ""
SAVE_FILE = ""
HOST_NAME = ""

ACCOUNT_KEY = "f03c6814-64e7-4183-8d30-08034a6cee97"
API_KEY = "0e57d0ea-5e8e-4955-922a-ee6e2dbd9a76"

logset_arr = []

loop = asyncio.get_event_loop()


def get_logsets_new(req):
    response = req.json()

    if req.status_code // 100 != 2:
        print("Got {}".format(req.status_code))

        if 'error' in response['response']:
            print(response['reason'])
            return

    logsets_size = len(response['list'])
    logset_count = 1

    print("logsets size = {}".format(logsets_size))

    for each_logset in response['list']:
        print(each_logset)

        print("Logset {}/{} name: {} \t - \t key: {}".format(
            logset_count, logsets_size, each_logset['name'], each_logset['key']))

        logset_count += 1

        logset_obj = logset.get_logset_from_payload(each_logset)

        logset_arr.append(logset_obj)


def get_logsets():
    req = requests.get("{}/{}/hosts/".format(LOGENTRIES_API_URL, ACCOUNT_KEY))
    response = req.json()

    if req.status_code // 100 != 2:
        print("Got {}".format(req.status_code))

        if 'error' in response['response']:
            print(response['reason'])
            return

    logsets_size = len(response['list'])
    logset_count = 1

    print("logsets size = {}".format(logsets_size))

    for each_logset in response['list']:
        print(each_logset)

        print("Logset {}/{} name: {} \t - \t key: {}".format(
            logset_count, logsets_size, each_logset['name'], each_logset['key']))

        logset_count += 1

        logset_obj = logset.get_logset_from_payload(each_logset)

        logset_arr.append(logset_obj)


def get_logs_from_logset_old():
    for each_logset in logset_arr:
        print(each_logset)

        req = requests.get("{}/{}/hosts/{}/".format(LOGENTRIES_API_URL, ACCOUNT_KEY, each_logset.key))
        response = req.json()

        for each_log in response['list']:
            if not each_log['key']:
                continue

            print(each_log)
            obj = logset.get_log_from_paylod(each_log)
            each_logset.add_log(obj)


def get_host_name(csv_file, name=None):
    HOST_NAMES_KEYS_DICT = {}
    req = requests.get("{}/{}/hosts/".format(LOGENTRIES_API_URL, ACCOUNT_KEY))
    response = req.json()
    if req.status_code // 100 != 2:
        print("Got {}".format(req.status_code))
        if 'error' in response['response']:
            print(response['reason'])
        return
    for hosts in response['list']:
        if name:
            print(hosts['name'] + "-" + hosts['key'])
            if hosts['name'] == name:
                HOST_NAMES_KEYS_DICT[hosts['key']] = hosts['name']
                break
        else:
            HOST_NAMES_KEYS_DICT[hosts['key']] = hosts['name']
    if HOST_NAMES_KEYS_DICT:
        with open(csv_file, 'w') as fp:
            OUTFILE_WRITER = csv.writer(fp)
            # OUTFILE_WRITER.writerow(['Log Set', 'Log Name', 'Query Result'])
            OUTFILE_WRITER.writerow(['Log Set', 'Log Name', 'From', 'To', 'Query Result'])
            for k, v in six.iteritems(HOST_NAMES_KEYS_DICT):
                if v != r'Inactivity Alerts':
                    get_log_name_and_key(OUTFILE_WRITER, k, v)


def get_le_url(url):
    header = {'x-api-key': API_KEY}
    return requests.get(url, headers=header)


def get_continuity_final_response(response):
    while True:
        response = get_le_url(response.json()['links'][0]['href'])
        if response.status_code != 200:
            return None
        if 'links' not in response.json():
            return response
        else:
            time.sleep(3)
            continue


def post_query_to_le(hostkey):
    headers = {'x-api-key': API_KEY}
    payload = {"logs": [hostkey],
               "leql": {"during": {"from": FROM_TS, "to": TO_TS},
                        "statement": SEARCH_QUERY}}
    return requests.post(LOGENTRIES_REST_URL, headers=headers, json=payload)


def handle_response(resp, log_key):
    time.sleep(3)
    if resp.status_code == 200:
        return resp
    elif resp.status_code == 202:
        print("Polling after 202")
        return get_continuity_final_response(resp)
    elif resp.status_code == 503:
        print("Retrying after 503 code")
        retried_response = post_query_to_le(log_key)
        return handle_response(retried_response, log_key)
    else:
        print('Error status code {} for host_key {}: {}'.format(
            resp.status_code, log_key, resp.content))
        return


def get_log_name_and_key(csv_writer, host_key, host_name):
    req = requests.get("{}/{}/hosts/{}/".format(LOGENTRIES_API_URL, ACCOUNT_KEY, host_key))
    response = req.json()
    for everylogkey in response['list']:
        if not everylogkey['key']:
            continue
        print("Querying {} {} with host_key {}".format(
            host_name, everylogkey['name'], everylogkey['key']))
        resp_log_query = post_query_to_le(str(everylogkey['key']))
        results = handle_response(resp_log_query, str(everylogkey['key']))
        if not results:
            break
        # if query is calculate(count) then: results.json()['statistics']['stats']['global_timeseries']['count']
        # if query is calculate(bytes) then: results.json()['statistics']['stats']['global_timeseries']['bytes']
        data = results.json()
        try:
            if len(data['statistics']['stats']['global_timeseries']) > 0:
                _bytes = data['statistics']['stats']['global_timeseries']['bytes']
                _bytes = humanizer.humanize_bytes(_bytes)
            else:
                _bytes = humanizer.humanize_bytes(0)
            hostkey = data['logs'][0]
            from_ts = humanizer.humanize_ts(data['leql']['during']['from'])
            to_ts = humanizer.humanize_ts(data['leql']['during']['to'])
            print("Log {} from {} to {} has {}".format(hostkey, from_ts, to_ts, _bytes))
            csv_writer.writerow((host_name, everylogkey['name'], from_ts, to_ts, _bytes))
        except KeyError as exc:
            print("Empty: {}".format(exc))


def set_timestamps(_from, _to):
    now_millis = int(round(time.mktime(_to.timetuple()) * 1000))
    epoch = int(time.mktime(_from.timetuple()))
    return now_millis, epoch * 1000


def start_by_console():
    def date(value):
        return datetime.datetime.strptime(value, '%d.%m.%Y').date()

    parser = argparse.ArgumentParser(description='Query Logentries API')

    parser.add_argument('--api-key', type=str, action='store',
                        default=os.environ.get('LOGENTRIES_API_KEY', "e4bececc-d1b4-449e-a949-2b6b7c5e0074"),
                        help='Logentries API_KEY (see README)')
    parser.add_argument('--account-key', type=str, action='store', required=True,
                        help='Logentries ACCOUNT_KEY (see README)')
    parser.add_argument('--host-name', type=str, action='store',
                        help='(optional) A Logentries Log set name')
    parser.add_argument('--from-date', type=date, action='store', required=True,
                        help='Retrieve log FROM this date (fmt: DD.MM.YYYY)')
    parser.add_argument('--to-date', type=date, action='store', default=datetime.date.today(),
                        help='(optional) Retrieve log TO this date (fmt: DD.MM.YYYY, default: today)')
    parser.add_argument('--save-file', type=str, action='store', default='results.csv',
                        help='(optional) CSV file to save results (default: results.csv)')
    args = parser.parse_args()

    ACCOUNT_KEY = args.account_key
    API_KEY = args.api_key
    TO_TS, FROM_TS = set_timestamps(args.from_date, args.to_date)

    SAVE_FILE = args.save_file

    HOST_NAME = args.host_name

    get_host_name(SAVE_FILE, HOST_NAME)

    print("{} saved.".format(SAVE_FILE))


if __name__ == '__main__':
    print("{} logentriesAPI.".format("Ahoy"))


def do_search(_from, _to):
    def date(value):
        return datetime.datetime.strptime(value, '%d.%m.%Y').date()

    set_timestamps(_from, _to)

    get_host_name(SAVE_FILE, HOST_NAME)

    print("{} saved.".format(SAVE_FILE))


def print_logs():
    for l in logset_arr:
        print(l.name)


def get_logs():
    if len(logset_arr) == 0:
        get_logsets()
    print_logs()
    # a = async_req.log_st(logset_arr)

    ahoy()
    future = asyncio.ensure_future(get_logs_async(logset_arr))
    loop.run_until_complete(future)

    return logset_arr


async def get_logs_async(lg_arr):
    tasks = []
    # create instance of Semaphore
    sem = asyncio.Semaphore(1000)

    # Create client session that will ensure we dont open new connection
    # per each request.
    async with ClientSession() as session:
        for each_logset in lg_arr:
            print(each_logset)

            url = "{}/{}/hosts/{}/".format(LOGENTRIES_API_URL, ACCOUNT_KEY, each_logset.key)
            print("fired: {}".format(url))
            # pass Semaphore and session to every GET request
            task = asyncio.ensure_future(bound_fetch(sem, url, session))
            tasks.append(task)

        responses = asyncio.gather(*tasks)
        await  responses
        a = responses
        if (a):
            print(a)

        print(a)


async def fetch(url, session):
    async with session.get(url) as response:
        delay = response.headers.get("DELAY")
        date = response.headers.get("DATE")
        # print("{}:{} with delay {}".format(date, response.url, delay))

        req = requests.get(response.url)
        print("fired  : {}".format(url))
        r = req.json()
        print("RECIVED: {}".format(url))
        # print(r)

        return r
        # return await r


async def bound_fetch(sem, url, session):
    # Getter function with semaphore.
    async with sem:
        # await get_logs_from_logset(url, session)
        await fetch(url, session)


async def get_logs_from_logset(url, session):
    req = requests.get(url)
    response = req.json()

    for each_log in response['list']:
        if not each_log['key']:
            continue

        print(each_log)
        obj = logset.get_log_from_paylod(each_log)
        # each_logset.add_log(obj)







def ahoy():
    url_arr = []
    for each_logset in logset_arr:
        print(each_logset)

        url = "{}/{}/hosts/{}/".format(LOGENTRIES_API_URL, ACCOUNT_KEY, each_logset.key)

        url_arr.append(url)

    rs = (grequests.get(u) for u in url_arr)

    for a in grequests.map(rs):
        print(a)
        b = a.json()

def get_log_n():
    url_arr = []
    #para cada url de log pegar os dados e colocar na tela
    #depoois de listado aparece a opção das queries