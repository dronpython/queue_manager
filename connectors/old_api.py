import requests
import json


def old_api_request(endpoint: str, req_type: str, req_body: dict, request_headers: dict) -> requests.Response:
    host = 'http://127.0.0.1'
    req = {'GET': requests.get,
           'POST': requests.post,
           'PUT': requests.put,
           'DELETE': requests.delete}
    port = '8070'
    url = f'{host}:{port}/{endpoint}'
    response = req[req_type](url=url, data=json.dumps(req_body), headers=request_headers)
    return response
