import json
import os
from logentriesAPI import api as api

from flask import Flask, render_template, request

# Flask app should start in global layout
app = Flask(__name__)


@app.route('/logentries', methods=['POST'])
def logentries():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    return req


@app.route('/logentries', methods=['GET'])
def logentries_get_logs():
    # req = request.get_json(silent=True, force=True)

    # print("Request:")

    api.ACCOUNT_KEY = "f03c6814-64e7-4183-8d30-08034a6cee97"
    api.API_KEY = "0e57d0ea-5e8e-4955-922a-ee6e2dbd9a76"

    api.get_logs()
    #
    # FROM_TS = datetime.date(2017, 10, 26)
    # TO_TS = datetime.date(2017, 10, 27)
    #
    # #a = datetime.datetime.strftime(FROM_TS, "DD.%MM.%YY")
    #
    # api.HOST_NAME = "portal-prod"
    #
    # api.SAVE_FILE = "result"
    #
    # api.LOGENTRIES_API_URL
    #
    # # api.do_search(FROM_TS, TO_TS)
    #
    # # Read/Write
    # # --api-key e4bececc-d1b4-449e-a949-2b6b7c5e0074
    # # Read Only
    # # --api-key 0e57d0ea-5e8e-4955-922a-ee6e2dbd9a76
    #
    # # --account-key f03c6814-64e7-4183-8d30-08034a6cee97
    # # --from-date 26.11.2017
    # # --to-date 27.11.2017
    # # --host-name portal-prod
    #
    # return "<h1>Patrick</h1>"


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')
