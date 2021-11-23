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
        'host': from_environ('QUEUE_DB_HOST'),
        'port': from_environ('QUEUE_DB_PORT'),
        'database': from_environ('QUEUE_DB_NAME'),
        'user': from_environ('QUEUE_DB_USER'),
        'password': from_environ('QUEUE_DB_PASSWORD')
    }
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
