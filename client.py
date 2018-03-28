# -*- coding: utf-8 -*-
'''
Created on 2017年4月14日

@author: chenyitao
'''
import logging
import os
import setproctitle

import gevent.monkey
gevent.monkey.patch_all()

from twisted.internet import reactor

log = logging.getLogger(__name__)
logging.getLogger('PIL').setLevel(logging.WARN)
from tddc import WorkerManager, TaskManager, DBSession, WorkerModel

from worker.spider_manager import Crawler


class CrawlerManager(WorkerManager):
    """
    classdocs
    """

    def __init__(self):
        """
        Constructor
        """
        log.info('Crawler Starting.')
        super(CrawlerManager, self).__init__()
        Crawler()
        TaskManager()
        log.info('Crawler Was Ready.')

    @staticmethod
    def start():
        if os.path.exists('./Worker.log'):
            os.remove('./Worker.log')
        if os.path.exists('./Scrapy.log'):
            os.remove('./Scrapy.log')
        setproctitle.setproctitle(DBSession.query(WorkerModel).get(1).platform)
        reactor.__init__()  # @UndefinedVariable
        CrawlerManager()
        reactor.run()  # @UndefinedVariable


def main():
    CrawlerManager.start()


if __name__ == '__main__':
    main()
