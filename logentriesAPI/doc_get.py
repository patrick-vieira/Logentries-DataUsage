import base64
import datetime
import hashlib
import hmac

import requests

resource_id = "<your_resource_id>"
api_key_id = "<your_api_key_id>"
api_key = "<your_api_key>"
uri = 'management/accounts/%s' % resource_id


def gensignature(api_key, date, content_type, request_method, query_path, request_body):
    encoded_hashed_body = base64.b64encode(hashlib.sha256(request_body).digest())
    canonical_string = request_method + content_type + date + query_path + encoded_hashed_body

    # Create a new hmac digester with the api key as the signing key and sha1 as the algorithm
    digest = hmac.new(api_key, digestmod=hashlib.sha1)
    digest.update(canonical_string)

    return digest.digest()


def create_headers():
    date_h = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    content_type_h = "application/json"
    method = 'GET'
    action = uri
    signature = gensignature(api_key, date_h, content_type_h, method, action, '')
    headers = {
        "Date": date_h,
        "Content-Type": content_type_h,
        "authorization-api-key": "%s:%s" % (api_key_id.encode('utf8'), base64.b64encode(signature))
    }
    print(headers)
    return headers


headers = create_headers()


def get_account():
    url = "https://rest.logentries.com/" + uri
    print(url)
    r = requests.request('GET', url, headers=headers)
    print(r.status_code, r.content)


def start():
    get_account()


if __name__ == '__main__':
    start()