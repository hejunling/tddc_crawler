# -*- coding: utf-8 -*-
'''
Created on 2017年4月14日
@author: chenyitao
'''
import logging

import gevent

from scrapy import signals
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from tddc import Singleton, TaskManager, Storager, Task, CacheManager, TaskCacheManager, TaskConfigModel, DBSession

# from config import ConfigCenterExtern
from .Scrapy import SingleSpider

settings = get_project_settings()
crawler_process = CrawlerProcess(settings)
crawler_process.join()

log = logging.getLogger(__name__)


class Crawler(object):
    '''
    classdocs
    '''
    __metaclass__ = Singleton

    def __init__(self):
        '''
        Constructor
        '''
        log.info('Spider Is Starting.')
        super(Crawler, self).__init__()
        self.task_conf = DBSession.query(TaskConfigModel).get(1)
        self.suspend_task_count = 0
        self._spider = None
        self._spider_mqs = None
        self._signals_list = {signals.spider_opened: self._spider_opened,
                              SingleSpider.SIGNAL_CRAWL_SUCCESSED: self._crawl_successed,
                              SingleSpider.SIGNAL_CRAWL_FAILED: self._crawl_failed}
        self._process = crawler_process
        self._process.crawl(SingleSpider, callback=self._spider_signals)
        
    def _get_spider_mqs_size(self):
        return len(self._spider_mqs) if self._spider_mqs else 0

    def _task_dispatch(self):
        size = self.task_conf.max_queue_size
        gevent.sleep(3)
        while True:
            if (self._get_spider_mqs_size() + self.suspend_task_count) < size / 4:
                while True:
                    task = TaskManager().get()
                    self._spider.add_task(task)
                    if self._get_spider_mqs_size() >= size:
                        break
            else:
                gevent.sleep(1)

    def _spider_signals(self, signal, *args, **kwargs):
        if signal not in self._signals_list.keys():
            return
        func = self._signals_list.get(signal, None)
        if func:
            func(*args, **kwargs)

    def _spider_opened(self, spider):
        if not self._spider:
            self._spider = spider
            self._spider_mqs = spider.crawler.engine.slot.scheduler.mqs
            gevent.spawn(self._task_dispatch)
            gevent.sleep()
            log.info('Spider Was Ready.')

    def _crawl_successed(self, task, data):
        TaskCacheManager().set_cache(task, data)
        task.status = Task.Status.CrawledSuccess
        TaskManager().task_successed(task)
        TaskManager().push_task(task,
                                self.task_conf.parser_topic)

    def _crawl_failed(self, task, status):
        task.status = status
        TaskManager().task_failed(task)
