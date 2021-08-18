import os
import csv
import json
import requests


# Mouser Base URL
BASE_URL = 'https://api.mouser.com/api/v1.0'


def get_api_keys(filename=None):
    """ Mouser API Keys """

    # Look for API keys in environmental variables
    api_keys = [
        os.environ.get('MOUSER_ORDER_API_KEY', ''),
        os.environ.get('MOUSER_PART_API_KEY', ''),
    ]

    # Else look into configuration file
    if not(api_keys[0] or api_keys[1]) and filename:
        try:
            with open(filename, 'r') as keys_in_file:
                api_keys = []

                for key in keys_in_file:
                    api_keys.append(key.replace('\n', ''))

                if len(api_keys) == 2:
                    return api_keys
                else:
                    pass
        except FileNotFoundError:
            print(f'[ERROR]\tAPI Keys File "{filename}" Not Found')

    return api_keys


class MouserAPIRequest:
    """ Mouser API Request """

    url = None
    api_url = None
    method = None
    body = {}
    response = None
    api_key = None

    def __init__(self, url, method, file_keys=None, *args):
        if not url or not method:
            return None
        self.api_url = BASE_URL + url
        self.method = method

        # Append argument
        if len(args) == 1:
            self.api_url += '/' + str(args[0])

        # Append API Key
        if self.name == 'Part Search':
            self.api_key = get_api_keys(file_keys)[1]
        else:
            self.api_key = get_api_keys(file_keys)[0]

        if self.api_key:
            self.url = self.api_url + '?apiKey=' + self.api_key

    def get(self, url):
        response = requests.get(url=url)
        return response

    def post(self, url, body):
        headers = {
            'Content-Type': 'application/json',
        }
        response = requests.post(url=url, data=json.dumps(body), headers=headers)
        return response

    def run(self, body={}):
        if self.method == 'GET':
            self.response = self.get(self.url)
        elif self.method == 'POST':
            self.response = self.post(self.url, body)

        return True if self.response else False

    def get_response(self):
        if self.response is not None:
            try:
                return json.loads(self.response.text)
            except json.decoder.JSONDecodeError:
                return self.response.text

        return {}

    def print_response(self):
        print(json.dumps(self.get_response(), indent=4, sort_keys=True))


class MouserBaseRequest(MouserAPIRequest):
    """ Mouser Base Request """

    name = ''
    allowed_methods = ['GET', 'POST']
    operation = None
    operations = {}

    def __init__(self, operation, file_keys=None, *args):
        ''' Init '''

        if operation not in self.operations:
            print(f'[{self.name}]\tInvalid Operation')
            print('-' * 10)
            
            valid_operations = [operation for operation, values in self.operations.items() if values[0] and values[1]]
            if valid_operations:
                print('Valid operations:')
                for operation in valid_operations:
                    print(f'- {operation}')
            return
            
        self.operation = operation
        (method, url) = self.operations.get(self.operation, ('', ''))

        if not url or not method or method not in self.allowed_methods:
            print(f'[{self.name}]\tOperation "{operation}" Not Yet Supported')
            return

        super().__init__(url, method, file_keys, *args)

    def export_csv(self, file_path: str, data: dict):
        ''' Export dictionary data to CSV '''

        with open(file_path, 'w') as csvfile:
            csvwriter = csv.writer(csvfile)

            for row in data:
                csvwriter.writerow(row)
