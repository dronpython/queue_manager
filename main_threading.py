import threading
import time
from queue import Queue
from threading import Thread
from connectors.old_api import old_api_request
from connectors.DBconnector import db

num_worker_threads = 3


def do_work(request):
    print("my task is", request, "i am ", threading.current_thread())
    rqid = request.rqid
    request_data = db.select_data('queue_requests', 'request_type', 'request_url',
                                  'request_headers', 'request_body',
                                  param_name='rqid', param_value=rqid)
    if request_data:
        try:
            response = old_api_request(request_data[0].request_url, request_data[0].request_type,
                                       request_data[0].request_body, request_data[0].request_headers)
            queue_status = 'DONE'
            resp_sc = str(response.status_code)
            resp_status = '200'  # response.status # ToDo Delete STATUS
            content = str(response.json()).replace("'", '"')

        except Exception as e:
            print(e)
            queue_status = 'ERROR'
            content = "{}"
            resp_sc = '500'
            resp_status = '500'

        db.insert_data('queue_responses', rqid, resp_sc, resp_status, content)
        db.update_data('queue_main', field_name='status', field_value=queue_status,
                       param_name='rqid', param_value=rqid)


def worker():
    while True:
        item = q.get()  # получаем задание из
        print("get task - ", item)
        do_work(item)  # выполняем работу
        q.task_done()  # сообщаем о завершении работы


def main():
    while True:
        start_time = time.time()
        print(f'Time: {start_time}')
        data = db.select_data('queue_main', 'rqid', param_name='status', param_value='PENDING')
        print(f"Нашли {len(data)} запросов")
        if data:
            for i in range(num_worker_threads):  # Создаем и запускаем потоки
                t = Thread(target=worker)
                t.setDaemon(True)
                t.start()
            for request in data:
                q.put(request)
            q.join()
            print(f'End time: {time.time() - start_time}')


if __name__ == '__main__':
    q = Queue()
    main()

# for i in range(num_worker_threads):  # Создаем и запускаем потоки
#     t = Thread(target=worker)
#     t.setDaemon(True)
#     t.start()
# for item in range(0, 5):  # помещаем задания в очередь
#     q.put(item)
# q.join()  # Ждем, пока не будут выполнены все задания
