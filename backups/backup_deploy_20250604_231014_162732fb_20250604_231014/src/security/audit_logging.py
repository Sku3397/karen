import logging
import datetime

class AuditLogger:
    def __init__(self):
        logging.basicConfig(filename='audit.log', level=logging.INFO)

    def log_action(self, user_id: str, action: str):
        time_stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logging.info(f"{time_stamp} - User: {user_id}, Action: {action}")