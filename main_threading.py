import os
import logging
from queue import Queue
from threading import Thread, enumerate, current_thread
from connectors.old_api import old_api_request
from connectors.DBconnector import db, query_dict


limit = 10
log_file = str(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'log.txt'))
logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
                    filename=log_file, level=logging.INFO)


def do_work(request):

    request_id = request.request_id
    # logging.info(f'Work at request_id {str(request_id)}. Thread number - {current_thread()}')
    request_data = db.select_data('queue_requests', 'request_type', 'request_url',
                                  'request_headers', 'request_body',
                                  param_name='request_id', param_value=request_id)
    # change status to 'working'
    db.update_data('queue_main', field_name='status', field_value='working',
                   param_name='request_id', param_value=request_id)

    if request_data:
        # do request
        # logging.info(f'Got request data {str(request_data)}. Sending request..')
        try:
            response = old_api_request(request_data[0].request_url, request_data[0].request_type,
                                       request_data[0].request_body, request_data[0].request_headers)
            # logging.info(f'Got response with status={str(response.status_code)} '
            #              f'and content={str(response.json())}')

            queue_status = 'done'
            response_status_code = str(response.status_code)
            content = str(response.json()).replace("'", '"')

        except Exception as e:
            # logging.error(f'Error: {str(e)}')
            queue_status = 'error'
            content = "{}"
            response_status_code = '500'

        # update tables
        db.insert_data('queue_responses', request_id, response_status_code, content)
        query = query_dict["update_main_then_finished"].format(request_id=request_id, status=queue_status)
        db.universal_update(query)

    else:
        query = query_dict["update_main_then_finished"].format(request_id=request_id, status='pending')
        db.universal_update(query)


def worker():
    item = q.get()  # получаем задание из
    do_work(item)  # выполняем работу
    q.task_done()  # сообщаем о завершении работы


def main():
    while True:
        data = db.universal_select(query_dict['select_new_requests'].format(limit))
        # data = db.select_data('queue_main', 'request_id', param_name='status', param_value='pending')
        if data:
            logging.info(f'{str(len(data))} requests found. Start working...')
            for i in range(len(data)):  # Создаем и запускаем потоки
                t = Thread(target=worker)
                t.setDaemon(True)
                t.start()
            for request in data:
                if len(enumerate()) > 1:  # 1 системный тред, остальные разгребают запросы
                    q.put(request)
            q.join()  # !Если в очереди окажется больше запросов чем выделилось потоков - зависнем!


if __name__ == '__main__':
    q = Queue()
    main()
