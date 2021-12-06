import logging
import logging.config
import yaml
from queue import Queue
from threading import Thread
from connectors.old_api import old_api_request
from connectors.DBconnector import db, query_dict
from integration import THREAD_COUNT, REQUEST_LIMIT

extra = {"source": "qmanager"}

with open('./logging_/config.yaml', 'r') as stream:
    config = yaml.load(stream, Loader=yaml.FullLoader)

logging.config.dictConfig(config)
logger = logging.getLogger(__name__)
logger = logging.LoggerAdapter(logger, extra)


def do_work(request):
    if request.request_headers:
        logger.info(f'Got request data {str(request)}. Sending request..')
        try:
            response = old_api_request(request.request_url, request.request_type,
                                       request.request_body, request.request_headers)
            logger.info(f'Got response with status={str(response.status_code)} '
                         f'and content={str(response.json())}')

            queue_status = 'done'
            response_status_code = str(response.status_code)
            content = str(response.json()).replace("'", '"')

        except Exception as e:
            logger.error(f'Error: {str(e)}')
            queue_status = 'error'
            content = "{}"
            response_status_code = '500'

        logger.info('Updating tables...')
        db.insert_data('queue_responses', request.request_id, response_status_code, content)
        query = query_dict["update_main_then_finished"].format(request_id=request.request_id, status=queue_status)
        db.universal_update(query)
        logger.info(f'Request {request.request_id} - finished!')

    else:
        logger.error(f'Request {str(request.request_id)} - no request data. Skip it')
        query = query_dict["update_main_then_finished"].format(request_id=request.request_id, status='pending')
        db.universal_update(query)


def worker():
    while True:
        item = q.get()  # получаем задание из
        do_work(item)  # выполняем работу
        q.task_done()  # сообщаем о завершении работы


def main():
    while True:
        data = db.universal_select(query_dict['select_new_requests'].format(REQUEST_LIMIT))
        logger.info('asdasd')
        if data:
            logger.info(f'{str(len(data))} requests found. Start working...')
            logger.info(f"Change status found requests to 'working'...")
            all_ids = tuple([request.request_id for request in data])
            db.universal_update(query_dict["change_status_to_working_by_id"].format(all_ids))
            for request in data:
                q.put(request)
            # q.join()


if __name__ == '__main__':
    q = Queue()
    for i in range(THREAD_COUNT):  # Создаем и запускаем потоки
        t = Thread(target=worker)
        t.start()
    main()
