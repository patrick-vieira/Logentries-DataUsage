# modified fetch function with semaphore
import random
import asyncio
from aiohttp import ClientSession

LOGENTRIES_API_URL = 'https://api.logentries.com'
LOGENTRIES_REST_URL = 'https://rest.logentries.com/query/logs/'
SEARCH_QUERY = "where(/.*/) calculate(bytes)"
ACCOUNT_KEY = ""
API_KEY = ""
TO_TS = ""
FROM_TS = ""
SAVE_FILE = ""
HOST_NAME = ""


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


def log_st(logset_arr):
    future = asyncio.ensure_future(get_logs(logset_arr))
    loop.run_until_complete(future)

    return ""


async def get_logs(logset_arr):
    tasks = []
    # create instance of Semaphore
    sem = asyncio.Semaphore(1000)

    # Create client session that will ensure we dont open new connection
    # per each request.
    async with ClientSession() as session:
        acc_key = "f03c6814-64e7-4183-8d30-08034a6cee97"
        api_key = "0e57d0ea-5e8e-4955-922a-ee6e2dbd9a76"

        for each_logset in logset_arr:
            print(each_logset)

            url = "{}/{}/hosts/{}/".format(LOGENTRIES_API_URL, acc_key, each_logset.key)

            # pass Semaphore and session to every GET request
            task = asyncio.ensure_future(bound_fetch(sem, url, session))
            tasks.append(task)

        responses = asyncio.gather(*tasks)
        await responses
#
#
# async def get_logs2(logset_arr):
#     async with ClientSession() as session:
#         for each_logset in logset_arr:
#             print(each_logset)
#             url = "{}/{}/hosts/{}/".format(LOGENTRIES_API_URL, ACCOUNT_KEY, each_logset.key)
#
#
#             async with session.get(url) as response:
#                 response = await response.read()
#                 print(response)
#
#
# async def get_log(url):
#     async with ClientSession() as session:
#         async with session.get(url) as response:
#             response = await response.read()
#             print(response)
#
#             log_arr = []
#             for each_log in response['list']:
#                 if not each_log['key']:
#                     continue
#                 log_arr.append(each_log)
#                 print(each_log)
#
