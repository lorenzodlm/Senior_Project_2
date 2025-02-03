import logging
import os

def setup_logging():
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Configure logging for each component
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
        },
        'handlers': {
            'door_lock': {
                'level': 'INFO',
                'formatter': 'standard',
                'class': 'logging.FileHandler',
                'filename': 'logs/door_lock.log',
                'mode': 'a',
            },
            'anti_spoofing': {
                'level': 'INFO',
                'formatter': 'standard',
                'class': 'logging.FileHandler',
                'filename': 'logs/anti_spoofing.log',
                'mode': 'a',
            },
            'main': {
                'level': 'INFO',
                'formatter': 'standard',
                'class': 'logging.FileHandler',
                'filename': 'logs/main.log',
                'mode': 'a',
            }
        },
        'loggers': {
            'door_lock': {
                'handlers': ['door_lock'],
                'level': 'INFO',
                'propagate': False
            },
            'anti_spoofing': {
                'handlers': ['anti_spoofing'],
                'level': 'INFO',
                'propagate': False
            },
            'main': {
                'handlers': ['main'],
                'level': 'INFO',
                'propagate': False
            }
        }
    }
    return logging_config