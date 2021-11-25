import os
import logging
from queue import Queue
from threading import Thread
from connectors.old_api import old_api_request
from connectors.DBconnector import db, query_dict

num_worker_threads = 3
log_file = str(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'log.txt'))
logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
                    filename=log_file, level=logging.INFO)


def do_work(request):

    request_id = request.request_id
    # logging.info('Work at request_id {}'.format(str(request_id)))
    logging.info(f'Work at request_id {str(request_id)}')
    request_data = db.select_data('queue_requests', 'request_type', 'request_url',
                                  'request_headers', 'request_body',
                                  param_name='request_id', param_value=request_id)
    if request_data:
        logging.info(f'Got request data {str(request_data)}. Sending request..')
        # logging.info('Got request data {}. Sending request..'.format(str(request_data)))
        try:
            response = old_api_request(request_data[0].request_url, request_data[0].request_type,
                                       request_data[0].request_body, request_data[0].request_headers)
            logging.info(f'Got response with status={str(response.status_code)} '
                         f'and content={str(response.json())}')
            # logging.info('Got response with status={} and content={}'.format(str(response.status_code),
            #                                                                  str(response.json())))
            queue_status = 'DONE'
            response_status_code = str(response.status_code)
            content = str(response.json()).replace("'", '"')

        except Exception as e:
            logging.error(f'Error: {str(e)}')
            # logging.error('Error: {}'.format(str(e)))
            queue_status = 'ERROR'
            content = "{}"
            response_status_code = '500'

        db.insert_data('queue_responses', request_id, response_status_code, content)
        # db.update_data('queue_main', field_name='status', field_value=queue_status,
        #                param_name='request_id', param_value=request_id)
        query = query_dict["update_main_then_finished"].format(request_id=request_id, status=queue_status)
        db.universal_update(query)



def worker():
    while True:
        item = q.get()  # получаем задание из
        do_work(item)  # выполняем работу
        q.task_done()  # сообщаем о завершении работы


def main():
    while True:
        data = db.select_data('queue_main', 'request_id', param_name='status', param_value='PENDING')
        if data:
            # logging.info('{} requests found. Start working...'.format(str(len(data))))
            logging.info(f'{str(len(data))} requests found. Start working...')
            for i in range(num_worker_threads):  # Создаем и запускаем потоки
                t = Thread(target=worker)
                t.setDaemon(True)
                t.start()
            for request in data:
                q.put(request)
            q.join()


if __name__ == '__main__':
    q = Queue()
    main()
