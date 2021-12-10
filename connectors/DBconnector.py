import logging
from psycopg2.extras import NamedTupleCursor
from psycopg2 import connect, DatabaseError
from integration import QUEUE_DB_CONFIG
from typing import Union

extra = {"source": "qmanager"}
logger = logging.getLogger(__name__)
logger = logging.LoggerAdapter(logger, extra)

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
              "change_status_to_working_by_id": "UPDATE queue_main SET status='working' where request_id in ('{}')"}


class DB:
    def __init__(self, database_config: dict):
        self.config = database_config
        self.conn = self._connect()

    def _connect(self):
        try:
            return connect(**self.config)
        except Exception as error:
            logger.error(error)
            return None

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

    def universal_insert(self, query):
        """ Вставка записи в базу данных."""
        with self._connect() as conn:
            try:
                cur = conn.cursor()
                cur.execute(query)
                conn.commit()
                cur.close()
            except (Exception, DatabaseError) as error:
                logger.error(error)

    def universal_update(self, query):
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
