import logging


class AppFilter(logging.Filter):
    def filter(self, record):
        record.source = 'qmanager'
        return True
