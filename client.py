# -*- coding: utf-8 -*-
'''
Created on 2017年4月14日

@author: chenyitao
'''

import gevent.monkey
gevent.monkey.patch_all()

from tddc.base import WorkerManager
from tddc.common import TDDCLogging
from twisted.internet import reactor

from worker.cookies import CookiesManager
from worker.proxy_pool import CrawlProxyPool
from worker.spider_manager import Crawler
from worker.storager import CrawlStorager
from worker.task import CrawlTaskManager
from crawler_site import CrawlerSite


class CrawlerManager(WorkerManager):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        TDDCLogging.info('->Crawler Starting.')
        super(CrawlerManager, self).__init__(CrawlerSite)
        self._crawler = Crawler()
        self._storager = CrawlStorager(CrawlerSite.random_hbase_node())
        self._proxy_pool = CrawlProxyPool()
        self._cookies = CookiesManager()
        self._task_manager = CrawlTaskManager()
        TDDCLogging.info('->Crawler Was Ready.')

    @staticmethod
    def start():
        reactor.__init__()  # @UndefinedVariable
        CrawlerManager()
        reactor.run()  # @UndefinedVariable


def main():
    CrawlerManager.start()

if __name__ == '__main__':
    main()
