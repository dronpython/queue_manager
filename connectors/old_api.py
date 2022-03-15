import requests
from integration import OLD_API_CONFIG, NEW_API_CONFIG

req = {'GET': requests.get,
       'POST': requests.post,
       'PUT': requests.put,
       'DELETE': requests.delete}


def api_request(endpoint: str, req_type: str, req_body: dict, request_headers: dict) -> requests.Response:
    new_api_endpoints = ['/bb/v6/create_repo', '/bb/v6/check_repo', '/bb/v6/project']

    new = False
    if endpoint in new_api_endpoints:
        new = True

    host = NEW_API_CONFIG['url'] if new else OLD_API_CONFIG['url']
    port = NEW_API_CONFIG['port'] if new else OLD_API_CONFIG['port']
    url = f'{host}:{port}{endpoint}'

    data = req_body if req_type == 'POST' else None
    params = req_body if req_type == 'GET' else None

    response = req[req_type](url=url, json=data, params=params, headers=request_headers)

    if response.status_code == 401:
        response = req[req_type](url=url, json=data, params=params, headers=request_headers)
    return response
