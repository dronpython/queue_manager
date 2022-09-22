import logging
from psycopg2.extras import NamedTupleCursor
from psycopg2 import connect, DatabaseError, OperationalError
from integration import QUEUE_DB_CONFIG
from typing import Union
from functools import wraps
from time import sleep
from contextlib import contextmanager


def backoff(start_sleep_time=0.1, factor=2, border_sleep_time=10, max_attempt_count=20):
    """
    Функция для повторного выполнения функции через некоторое время, если возникла ошибка.
    Использует наивный экспоненциальный рост времени повтора (factor)
    до граничного времени ожидания (border_sleep_time)

    Формула:
        t = start_sleep_time * 2^(n) if t < border_sleep_time
        t = border_sleep_time if t >= border_sleep_time
    :param start_sleep_time: начальное время повтора
    :param factor: во сколько раз нужно увеличить время ожидания
    :param border_sleep_time: граничное время ожидания
    :param max_attempt_count: максимальное кол-во попыток

    :return: результат выполнения функции
    """

    def func_wrapper(func):
        n = 0
        t = 0

        @wraps(func)
        def inner(self, *args, **kwargs):
            nonlocal n, t
            a = None
            while not a:
                if n == max_attempt_count:
                    logger.info("Rich max attempt connection count. Close program.")
                    raise Exception("Connect exception error")
                try:
                    logger.info("Trying to connect to db")
                    a = func(self, **kwargs)
                    logger.info("DB successfully connected")
                except OperationalError:
                    n += 1
                    t = start_sleep_time * factor ** n if t < border_sleep_time else border_sleep_time
                    logger.error("Connection error", exc_info=True)
                    sleep(t)
            return a
        return inner
    return func_wrapper

logger = logging.getLogger(__name__)

query_dict = {"select_new_requests": """SELECT qm.request_id, domain, qm.username, qr.request_type, 
                                               qr.request_url, qr.request_body, qr.request_headers
                                        FROM queue_main qm
                                        JOIN queue_requests qr on qm.request_id = qr.request_id
                                        WHERE qm.status = 'pending'
                                        AND qm.work_count < 3
                                        ORDER BY qm.timestamp
                                        LIMIT {}""",
              "update_main_then_finished": """UPDATE queue_main
                                              SET status = '{status}', work_count = work_count + 1
                                              WHERE request_id = '{request_id}'""",
              "change_status_to_working_by_id": "UPDATE queue_main SET status='working' where request_id in ('{}')",
              "insert_or_update_data": """UPDATE queue_responses SET response_status_code='{status}', response_body='{body}' 
                                          WHERE request_id='{request_id}';
                                          INSERT INTO queue_responses (request_id, response_status_code, response_body)
                                          SELECT '{request_id}', '{status}', '{body}'
                                          WHERE NOT EXISTS (SELECT 1 FROM queue_responses WHERE request_id='{request_id}');"""}


class DB:
    def __init__(self, database_config: dict):
        self.config = database_config
        self.conn = self._connect()

    @backoff(start_sleep_time=0.2, factor=2, border_sleep_time=10)
    @contextmanager
    def _connect(self):
        conn: _connection = connect(**self.config)
        yield conn
        logger.info("Closing connection")
        conn.close()

    def select_data(self, table, *args, param_name: Union[str, int] = 1, param_value: Union[str, int] = 1):
        """Выборка записей из базы данных."""
        with self._connect() as conn:
            try:
                cur = conn.cursor(cursor_factory=NamedTupleCursor)
                select_arguments = '","'.join(args)
                select_string = 'SELECT "{}" FROM {} WHERE {}={}' if isinstance(param_name, int) \
                    else 'SELECT "{}" FROM {} WHERE "{}"=\'{}\''
                select_query = select_string.format(select_arguments, table, param_name, param_value)
                cur.execute(select_query)
                query_result = cur.fetchall()
                cur.close()
            except (Exception, DatabaseError) as error:
                logger.error(error)
                query_result = None
            return query_result

    def insert_data(self, table, *args):
        """Добавление записи в базу данных."""
        with self._connect() as conn:
            try:
                cur = conn.cursor()
                insert_arguments = "','".join(args)
                insert_string = "INSERT INTO {} VALUES(DEFAULT,'{}')"
                insert_query = insert_string.format(table, insert_arguments)
                cur.execute(insert_query)
                conn.commit()
                cur.close()
            except (Exception, DatabaseError) as error:
                logger.error(error)

    def update_data(self, table, **kwargs):
        """ Обновленме записи в базе данных."""
        with self._connect() as conn:
            try:
                cur = conn.cursor()
                insert_string = 'UPDATE {} SET "{}"=\'{}\' WHERE "{}"=\'{}\''
                insert_query = insert_string.format(table, kwargs['field_name'], kwargs['field_value'],
                                                    kwargs['param_name'], kwargs['param_value'])
                cur.execute(insert_query)
                conn.commit()
                cur.close()
            except (Exception, DatabaseError) as error:
                logger.error(error)

    def universal_select(self, query):
        """Выборка записей из базы данных."""
        with self._connect() as conn:
            try:
                cur = conn.cursor(cursor_factory=NamedTupleCursor)
                cur.execute(query)
                data = cur.fetchall()
                cur.close()
            except (Exception, DatabaseError) as error:
                logger.error(error)
                data = None
            finally:
                return data

    def universal_db_request(self, query):
        """ Обновленме записи в базе данных."""
        with self._connect() as conn:
            try:
                cur = conn.cursor()
                cur.execute(query)
                conn.commit()
                cur.close()
            except (Exception, DatabaseError) as error:
                logger.error(error)


db = DB(QUEUE_DB_CONFIG)
