# logger_config.py

import logging

def setup_logger():
    # Configuración del logger
    logging.basicConfig(
        filename='app.log',
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',  # Formato del mensaje de log
    )