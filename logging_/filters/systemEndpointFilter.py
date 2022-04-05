import logging


class SystemEndpointFilter(logging.Filter):
    """Добавляет источник логов."""
    def filter(self, record):
        record.system_ep = "NULL" if not hasattr(record, "system_ep") else record.system_ep
        return True
