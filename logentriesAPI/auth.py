import sys
import hashlib, hmac
import base64
import datetime
import requests

if (len(sys.argv) < 6):
    print("Usage: ")
    print("gen_signature <api_key> <api_key_id> <method> <uri> <body>")
    exit()


def gensignature(api_key, date, content_type, request_method, query_path, request_body):
    hashed_body = base64.b64encode(hashlib.sha256(request_body).digest())

    canonical_string = request_method + content_type + date + query_path + hashed_body

    # Create a new hmac digester with the api key as the signing key and sha1 as the algorithm
    digest = hmac.new(api_key, digestmod=hashlib.sha1)
    digest.update(canonical_string)

    return digest.digest()


if __name__ == '__main__':
    print('Usage is: api_key apikeyid method path body')
    date_h = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    content_type_h = "application/json"

    method =    sys.argv[3]
    uri = sys.argv[4]
    body = sys.argv[5]

    url = "https://rest.logentries.com/" + uri

    # Remove the query parameters
    action = uri.split("?")[0]
    signature = gensignature(sys.argv[1], date_h, content_type_h, method, action, body)

    headers = {
        "Date": date_h,
        "Content-Type": content_type_h,
        "authorization-api-key": "%s:%s" % (sys.argv[2].encode('utf8'), base64.b64encode(signature))
    }

    print("Sending %s request to %s with body='%s'" % (method, url, body))
    print("headers = '%s'" % headers)

    r = requests.request(method, url, data=body, headers=headers)
    print(r.status_code, r.content)
