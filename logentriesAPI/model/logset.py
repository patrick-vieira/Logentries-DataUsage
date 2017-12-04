
class log(object):
    # {'key': '585dc9bc-b476-4c16-a7cf-a669a0b39a6b', 'follow': 'false', 'token': '1002c50d-f03b-4f38-af2c-0bfa23211e93',
    #  'retention': -1, 'type': 'token', 'object': 'log', 'filename': '', 'name': 'Deliveries', 'created': 1413741736152}

    def __init__(self, name, key):
        self.name = name
        self.key = key
        self.type = None
        self.token = None

    def set_type(self, type):
        self.type = type

    def set_token(self, token):
        self.token = token


class logset(object):

    def __init__(self, name, key):
        self.name = name
        self.key = key
        self.logs = []

    def add_log(self, log):
        self.logs.append(log)


def get_logset_from_payload(dct):
    return logset(dct['name'], dct['key'])


def get_log_from_paylod(dct):
    return log(dct['name'], dct['key'])


