import json

import asyncio
import requests
import sys

from aiohttp import ClientSession

from logentriesAPI.model import logset

LOGENTRIES_API_URL = 'https://api.logentries.com'

ACCOUNT_KEY = "f03c6814-64e7-4183-8d30-08034a6cee97"

logset_arr = {}


def get_host_name(csv_file, name=None):
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
                logset_arr[hosts['key']] = hosts['name']
                break
        else:
            logset_arr[hosts['key']] = hosts['name']
    if logset_arr:
        with open(csv_file, 'w') as fp:
            OUTFILE_WRITER = csv.writer(fp)
            # OUTFILE_WRITER.writerow(['Log Set', 'Log Name', 'Query Result'])
            OUTFILE_WRITER.writerow(['Log Set', 'Log Name', 'From', 'To', 'Query Result'])
            for k, v in six.iteritems(logset_arr):
                if v != r'Inactivity Alerts':
                    get_log_name_and_key(OUTFILE_WRITER, k, v)



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


async def fetch(url, session):
    async with session.get(url) as response:
        delay = response.headers.get("DELAY")
        date = response.headers.get("DATE")
        print("{}:{} with delay {}".format(date, response.url, delay))
        print(response.read())
        return await response.read()


async def bound_fetch(sem, url, session):
    # Getter function with semaphore.
    async with sem:
        await fetch(url, session)


async def run(r):
    url = "http://localhost:5000/{}"
    tasks = []
    # create instance of Semaphore
    sem = asyncio.Semaphore(1000)

    # Create client session that will ensure we dont open new connection
    # per each request.
    async with ClientSession() as session:
        for i in range(r):
            # pass Semaphore and session to every GET request
            task = asyncio.ensure_future(bound_fetch(sem, url.format(i), session))
            tasks.append(task)

        responses = asyncio.gather(*tasks)
        await responses


number = 10000
loop = asyncio.get_event_loop()
if __name__ == '__main__':
    future = asyncio.ensure_future(run(number))
    loop.run_until_complete(future)

if __name__ == '__main__':
    try:
        get_logsets()
        future = asyncio.ensure_future(run(number))
        loop.run_until_complete(future)

    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise
