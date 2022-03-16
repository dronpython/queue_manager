import os


def from_environ(name, default=None, allow_none=False):
    envname = f"[{name}]"
    try:
        var = os.environ[name]
        return var
    except Exception as e:
        print(e)
        if not allow_none:
            raise Exception("ENV variable not found: " + envname)
        else:
            return default


try:
    QUEUE_DB_CONFIG = {
        'host': from_environ('db_host'),
        'port': from_environ('db_port'),
        'database': from_environ('db_name'),
        'user': from_environ('db_user'),
        'password': from_environ('db_password')
    }

    OLD_API_CONFIG = {
        'url': from_environ('old_api_url'),
        'port': from_environ('old_api_port'),
    }
    NEW_API_CONFIG = {
        'url': from_environ('new_api_url'),
        'port': from_environ('new_api_port'),
    }

    DB_TEST_CREEDS = {
        'host': from_environ('db_host'),
        'port': from_environ('db_port'),
        'database': from_environ('db_name'),
        'user': from_environ('db_user'),
        'password': from_environ('db_password')
    }

    REQUEST_LIMIT = from_environ('request_limit')
    THREAD_COUNT = from_environ('thread_count')
    # raise Exception

except Exception as EE:
    try:
        print('>>>INTEGRATION EXCEPTION!!!')
        print('>>>', EE)
        print('>>>INTEGRATION TRY TO LOAD LOCAL ENV!!!')
        from integration_local import *

    except Exception as EE1:
        print('>>>INTEGRATION_LOCAL EXCEPTION!!!')
        print('>>>', EE1)
