import logging.config as cfg
import logging
import yaml
import json
from queue import Queue
from threading import Thread, current_thread
from connectors.old_api import api_request
from connectors.DBconnector import db, query_dict
from integration import THREAD_COUNT, REQUEST_LIMIT
from time import sleep
from contextvars import ContextVar


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id.get()
        return True


with open('./logging_/config.yaml', 'r') as stream:
    config = yaml.load(stream, Loader=yaml.FullLoader)


cfg.dictConfig(config)

logger = logging.getLogger(__name__)
request_id: ContextVar[str] = ContextVar('request_id', default='service')

logger.addFilter(RequestIdFilter())


def do_work(request):
    request_id.set(str(request.request_id))
    log_info = f'request_id={str(request.request_id)}: '
    if request.request_headers:
        logger.info(f'{log_info}Thread - {current_thread()}. '
                    f'Got request data {str(request)}. '
                    f'Sending request..')
        response = None
        try:
            request.request_headers.update({"X-Request-Id": request_id.get()})
            response = api_request(request.request_url, request.request_type,
                                   request.request_body, request.request_headers)
            logger.info(f'{log_info}Got response status={str(response.status_code)}.'
                        f'Content={str(response.json())}')

            queue_status = 'done'
            response_status_code = str(response.status_code)
            content = json.dumps(response.json())

        except Exception as e:
            logger.error(f'Error: {str(e)}')
            queue_status = 'error'
            content = json.dumps(response.json()) if response else '{}'
            content.replace("'", "''")
            response_status_code = str(response.status_code) if response else '520'

        logger.info(f'{log_info}Updating tables...')
        db.insert_data('queue_responses', request.request_id, response_status_code, content)
        query = query_dict["update_main_then_finished"].format(request_id=request.request_id,
                                                               status=queue_status)
        db.universal_update(query)
        logger.info(f'{log_info} Finished!')

    else:
        logger.error(f'{log_info}No request data. Skip it')
        query = query_dict["update_main_then_finished"].format(request_id=request.request_id,
                                                               status='pending')
        db.universal_update(query)


def worker():
    while True:
        item = q.get()  # получаем задание из
        do_work(item)  # выполняем работу
        q.task_done()  # сообщаем о завершении работы


def main():
    while True:
        data = db.universal_select(query_dict['select_new_requests'].format(int(REQUEST_LIMIT)))
        if data:
            logger.info(f'{str(len(data))} requests found. Start working...')
            logger.info(f"Change status found requests to 'working'...")
            all_ids = "','".join(str(request.request_id) for request in data)
            db.universal_update(query_dict["change_status_to_working_by_id"].format(all_ids))
            for request in data:
                q.put(request)
            sleep(1)


if __name__ == '__main__':
    q = Queue()
    for i in range(int(THREAD_COUNT)):  # Создаем и запускаем потоки
        t = Thread(target=worker)
        t.start()
    main()
