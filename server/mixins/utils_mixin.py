import logging
import sys

from server.mixins.base_mixin import BaseMixin


class UtilsMixin(BaseMixin):
    def setup_logger(self, name, level=logging.INFO, log_file=None):
        """Настройка логгера с выводом в консоль и файл."""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_formatter = logging.Formatter('[%(levelname)s] %(message)s')

        if not log_file is None:
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)

        self.logger.addHandler(console_handler)

        return self.logger