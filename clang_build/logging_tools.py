import logging as _logging
import tqdm as _tqdm

_LOGGER = _logging.getLogger("clang_build.clang_build")

class TqdmHandler(_logging.StreamHandler):
    def __init__(self):
        _logging.StreamHandler.__init__(self)

    def emit(self, record):
        msg = self.format(record)
        _tqdm.tqdm.write(msg)

class NamedLoggerAdapter(_logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return '[[%s]]: %s' % (self.extra['tree_element'].identifier, msg), kwargs

class NamedLogger:
    def __init__(self):
        self._logger = NamedLoggerAdapter(_LOGGER, {'tree_element': self})

    def log_message(self, message: str) -> str:
        """
        """
        return f"[[{self.__repr__()}]]: {message}"
