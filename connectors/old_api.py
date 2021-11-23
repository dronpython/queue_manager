import requests
import json
from integration import OLD_API_CONFIG

req = {'GET': requests.get,
       'POST': requests.post,
       'PUT': requests.put,
       'DELETE': requests.delete}


def old_api_request(endpoint: str, req_type: str, req_body: dict, request_headers: dict) -> requests.Response:
    host = OLD_API_CONFIG['url']
    port = OLD_API_CONFIG['port']
    url = f'{host}:{port}/{endpoint}'
    response = req[req_type](url=url, data=json.dumps(req_body), headers=request_headers)
    return response
