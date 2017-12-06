import os
import argparse
import requests
import time
import datetime
import csv
import six

from commons import humanizer

LOGENTRIES_API_URL = 'https://api.logentries.com'
LOGENTRIES_REST_URL = 'https://rest.logentries.com/query/logs/'
SEARCH_QUERY = "where(/.*/) calculate(bytes)"


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
    now_millis = int(round(time.mktime(date(_to).timetuple()) * 1000))
    epoch = int(time.mktime(date(_from).timetuple()))
    return now_millis, epoch * 1000


if __name__ == '__main__':
    global ACCOUNT_KEY, API_KEY, TO_TS, FROM_TS


    def date(value):
        return datetime.datetime.strptime(value, '%d.%m.%Y').date()


    api_key = "e4bececc-d1b4-449e-a949-2b6b7c5e0074"
    account_key = "f03c6814-64e7-4183-8d30-08034a6cee97"
    from_date = "26.11.2017"
    to_date = "27.11.2017"
    host_name = "portal-prod"
    save_file = "report"

    ACCOUNT_KEY = account_key
    API_KEY = api_key
    TO_TS, FROM_TS = set_timestamps(from_date, to_date)
    get_host_name(save_file, host_name)
    print("{} saved.".format(save_file))
