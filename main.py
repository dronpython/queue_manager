from connectors.old_api import old_api_request
from time import sleep, time
from connectors.DBconnector import db
import os
import logging

log_file = str(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'log.txt'))
logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
                    filename=log_file, level=logging.INFO)


if __name__ == "__main__":
    start_time = time()
    while True:
        data = db.select_data('queue_main', 'request_id', param_name='status', param_value='pending')
        # ToDo check priority
        if data:
            # logging.info(f'{str(len(data))} requests found. Start working...')
            logging.info('{} requests found. Start working...'.format(str(len(data))))
            for request in data:
                request_id = request.request_id
                logging.info('Work at request_id {}'.format(str(request_id)))
                request_data = db.select_data('queue_requests', 'request_type', 'request_url',
                                              'request_headers', 'request_body',
                                              param_name='request_id', param_value=request_id)
                if request_data:
                    # ToDo if no request data infinity loop - fix!
                    logging.info('Got request data {}. Sending request..'.format(str(request_data)))
                    try:
                        response = old_api_request(request_data[0].request_url, request_data[0].request_type,
                                                   request_data[0].request_body, request_data[0].request_headers)
                        logging.info('Got response with status={} and content={}'.format(str(response.status_code),
                                                                                         str(response.json())))
                        queue_status = 'done'
                        resp_sc = str(response.status_code)
                        resp_status = '200'  # response.status # ToDo Delete STATUS
                        content = str(response.json()).replace("'", '"')

                    except Exception as e:
                        logging.error('Error: {}'.format(str(e)))
                        queue_status = 'error'
                        content = "{}"
                        resp_sc = '500'
                        resp_status = '500'
                        # ToDo return 500 status code

                    db.insert_data('queue_responses', request_id, resp_sc, resp_status, content)
                    db.update_data('queue_main', field_name='status', field_value=queue_status,
                                   param_name='request_id', param_value=request_id)
            print(time()-start_time)