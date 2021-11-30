import logging
from logging import config
from queue import Queue
from threading import Thread
from connectors.old_api import old_api_request
from connectors.DBconnector import db, query_dict

num_threads = 10
limit = 100
logging.config.fileConfig('log.ini')


def do_work(request):
    logging.info(f"Change status request_id {str(request.request_id)} to 'working'")
    db.update_data('queue_main', field_name='status', field_value='working',
                   param_name='request_id', param_value=request.request_id)

    if request.request_headers:
        logging.info(f'Got request data {str(request)}. Sending request..')
        try:
            response = old_api_request(request.request_url, request.request_type,
                                       request.request_body, request.request_headers)
            logging.info(f'Got response with status={str(response.status_code)} '
                         f'and content={str(response.json())}')

            queue_status = 'done'
            response_status_code = str(response.status_code)
            content = str(response.json()).replace("'", '"')

        except Exception as e:
            logging.error(f'Error: {str(e)}')
            queue_status = 'error'
            content = "{}"
            response_status_code = '500'

        logging.info('Updating tables...')
        db.insert_data('queue_responses', request.request_id, response_status_code, content)
        query = query_dict["update_main_then_finished"].format(request_id=request.request_id, status=queue_status)
        db.universal_update(query)
        logging.info(f'Request {request.request_id} - finished!')

    else:
        logging.error(f'Request {str(request.request_id)} - no request data. Skip it')
        query = query_dict["update_main_then_finished"].format(request_id=request.request_id, status='pending')
        db.universal_update(query)


def worker():
    while True:
        item = q.get()  # получаем задание из
        do_work(item)  # выполняем работу
        q.task_done()  # сообщаем о завершении работы


def main():
    while True:
        data = db.universal_select(query_dict['select_new_requests'].format(limit))
        if data:
            logging.info(f'{str(len(data))} requests found. Start working...')
            for request in data:
                q.put(request)
            q.join()


if __name__ == '__main__':
    q = Queue()
    for i in range(num_threads):  # Создаем и запускаем потоки
        t = Thread(target=worker)
        t.setDaemon(True)
        t.start()
    main()
