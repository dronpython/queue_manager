from connectors.old_api import old_api_request
# from time import sleep, time
from connectors.DBconnector import db
import os
import logging

log_file = str(os.path.join(os.path.dirname(os.path.realpath(__file__)), "logs/log.txt"))
logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
                    filename=log_file, level=logging.INFO)


if __name__ == "__main__":
    while True:
        data = db.select_data('queue_main', 'rqid', param_name='status', param_value='PENDING')
        # ToDo check priority, increase work_count
        if data:
            logging.info(f'{len(data)} requests found. Start working...')
            for request in data:
                rqid = request.rqid
                logging.info(f'Work at request_id {str(rqid)}')
                request_data = db.select_data('queue_requests', 'request_type', 'request_url',
                                              'request_headers', 'request_body',
                                              param_name='rqid', param_value=rqid)
                if request_data:
                    logging.info(f'Got request data {str(request_data)}. Sending request..')
                    try:
                        response = old_api_request(request_data[0].request_url, request_data[0].request_type,
                                                   request_data[0].request_body, request_data[0].request_headers)
                        logging.info(f'Got response with status={str(response.status_code)} '
                                     f'and content={str(response.json())}')
                        queue_status = 'DONE'
                        resp_sc = str(response.status_code)
                        resp_status = '200'  # response.status # ToDo Delete STATUS
                        content = str(response.json()).replace("'", '"')

                    except Exception as e:
                        logging.error(f'Error: {str(e)}')
                        queue_status = 'ERROR'
                        content = "{}"
                        resp_sc = '500'
                        resp_status = '500'
                        # ToDo return 500 status code

                    db.insert_data('queue_responses', rqid, resp_sc, resp_status, content)
                    db.update_data('queue_main', field_name='status', field_value=queue_status,
                                   param_name='rqid', param_value=rqid)
