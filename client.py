# -*- coding: utf-8 -*-
'''
Created on 2017年4月14日

@author: chenyitao
'''

import os
import setproctitle
import worker.log_extern

import gevent.monkey
gevent.monkey.patch_all()

from twisted.internet import reactor

from tddc import WorkerManager, Storager, TaskManager

from config import ConfigCenterExtern
from worker.spider_manager import Crawler


class CrawlerManager(WorkerManager):
    """
    classdocs
    """

    def __init__(self):
        """
        Constructor
        """
        super(CrawlerManager, self).__init__()
        self.info('Crawler Starting.')
        Crawler()
        TaskManager()
        self.info('Crawler Was Ready.')

    @staticmethod
    def start():
        if os.path.exists('./Worker.log'):
            os.remove('./Worker.log')
        if os.path.exists('./Scrapy.log'):
            os.remove('./Scrapy.log')
        ConfigCenterExtern()
        setproctitle.setproctitle(ConfigCenterExtern().get_worker().name)
        reactor.__init__()  # @UndefinedVariable
        CrawlerManager()
        reactor.run()  # @UndefinedVariable


def main():
    CrawlerManager.start()


if __name__ == '__main__':
    main()
