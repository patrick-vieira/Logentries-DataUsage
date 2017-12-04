import grequests

urls = [
    'http://www.heroku.com',
    'http://tablib.org',
    'http://httpbin.org',
    'http://python-requests.org',
    'http://kennethreitz.com'
]

if __name__ == '__main__':
    rs = (grequests.get(u) for u in urls)

    for a in grequests.map(rs):
        print(a)
        b = a
    print(rs)