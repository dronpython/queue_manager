# from configparser import ConfigParser
from psycopg2.extras import NamedTupleCursor
from psycopg2 import connect, DatabaseError
from integration import QUEUE_DB_CONFIG
from typing import Union

query_dict = {"select_new_requests": """SELECT qm.rqid, domain, author, request_type, request_url, request_body  
                                        FROM queue_main qm
                                        JOIN queue_requests qr on qm.rqid = qr.rqid
                                        WHERE qm.status = 'PENDING'
                                        ORDER BY qm.timestamp"""}


# def config(filename='database.ini', section='postgresql'):
#     # create a parser
#     parser = ConfigParser()
#     # read config file
#     parser.read(filename)
#
#     # get section, default to postgresql
#     db = {}
#     if parser.has_section(section):
#         params = parser.items(section)
#         for param in params:
#             db[param[0]] = param[1]
#     else:
#         raise Exception('Section {0} not found in the {1} file'.format(section, filename))
#     return db


class DB:
    def __init__(self, database_config: dict):
        self.config = database_config
        self.conn = self._connect()

    def _connect(self):
        try:
            return connect(**self.config)
        except Exception as error:
            print(error)
            print(error.__traceback__)
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
                print(error)
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
                print(error)

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
                print(error)
    # def _close_connection(self):
    #     return self.conn.close()


db = DB(QUEUE_DB_CONFIG)
# data = db.select_data('queue_main', 'rqid', 'status', param_name="status", param_value="PENDING")
# print(data)


# def update_queue(request_id: str, request_status: str, resp_sc: int, resp_status: str, resp_body: dict):
#     """ Connect to the PostgreSQL database server """
#     conn = None
#     resp_body = str(resp_body).replace("'", '"')
#     try:
#         params = config()
#         conn = connect(**params)
#         cur = conn.cursor()
#         cur.execute(f"UPDATE queue_main SET status = '{request_status}' WHERE rqid = '{request_id}'")
#         cur.execute(f"INSERT INTO queue_responses(rqid, response_status_code, response_status, response_body)
#         VALUES('{request_id}', '{resp_sc}', '{resp_status}', '{resp_body}')")
#         conn.commit()
#         cur.close()
#     except (Exception, DatabaseError) as error:
#         print(error)
#     finally:
#         if conn is not None:
#             conn.close()
#             print('Database connection closed.')
#
#
# def select_function(query):
#     """ Connect to the PostgreSQL database server """
#     conn = None
#     try:
#         params = config()
#         conn = connect(**params)
#         cur = conn.cursor(cursor_factory=NamedTupleCursor)
#         cur.execute(query)
#         data = cur.fetchall()
#         print(data)
#         cur.close()
#         return data
#     except (Exception, DatabaseError) as error:
#         print(error)
#     finally:
#         if conn is not None:
#             conn.close()
#             print('Database connection closed.')
#
#
# def get_request_by_uuid(uuid: str):
#     """ Connect to the PostgreSQL database server """
#     conn = None
#     try:
#         params = config()
#         conn = connect(**params)
#         cur = conn.cursor(cursor_dactory=DictCursor)
#         cur.execute(f"SELECT * from queue_requests WHERE rqid = '{uuid}'")
#         data = cur.fetchone()
#         cur.close()
#         return data
#     except (Exception, DatabaseError) as error:
#         print(error)
#     finally:
#         if conn is not None:
#             conn.close()
#             print('Database connection closed.')
