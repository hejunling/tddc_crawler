# -*- coding: utf-8 -*-
"""
Created on 2017年8月31日

@author: chenyitao
"""

import sys
import logging

sys.stderr = sys.stdout
logging.CRITICAL = 35
logging.FATAL = logging.CRITICAL
logging.ERROR = 35
logging.WARNING = 33
logging.WARN = logging.WARNING
logging.INFO = 32
logging.DEBUG = 31
logging.NOTSET = 0

logging._levelNames = {
    logging.CRITICAL: 'CRITICAL',
    logging.ERROR: 'ERROR',
    logging.WARNING: 'WARNING',
    logging.INFO: 'INFO',
    logging.DEBUG: 'DEBUG',
    logging.NOTSET: 'NOTSET',
    'CRITICAL': logging.CRITICAL,
    'ERROR': logging.ERROR,
    'WARN': logging.WARNING,
    'WARNING': logging.WARNING,
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG,
    'NOTSET': logging.NOTSET,
}


logging.basicConfig(format=('[%(asctime)s] [%(levelname)s] '
                            '[%(name)s:%(lineno)s:%(funcName)s] '
                            ' )=> %(message)s'),
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.DEBUG,
                    filename='Scrapy.log')


def _log_extra(self, level, msg, args, exc_info=None, extra=None):
    """
    Low-level logging routine which creates a LogRecord and then calls
    all the handlers of this logger to handle the record.
    """
    # if 'kafka' in self.name or 'happybase' in self.name:
    #     return
    if logging._srcfile:
        # IronPython doesn't track Python frames, so findCaller raises an
        # exception on some versions of IronPython. We trap it here so that
        # IronPython can use logging.
        try:
            fn, lno, func = self.findCaller()
        except ValueError:
            fn, lno, func = "(unknown file)", 0, "(unknown function)"
    else:
        fn, lno, func = "(unknown file)", 0, "(unknown function)"
    if exc_info:
        if not isinstance(exc_info, tuple):
            exc_info = sys.exc_info()
    record = self.makeRecord(self.name, level, fn, lno, msg, args, exc_info, func, extra)
    self.handle(record)


logging.Logger._log = _log_extra
