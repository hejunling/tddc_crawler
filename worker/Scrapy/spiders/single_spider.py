# -*- coding:utf-8 -*-
'''
Created on 2015年12月28日

@author: chenyitao
'''
import logging
import random

import gevent.queue
from scrapy import signals
import scrapy
from scrapy.exceptions import DontCloseSpider
from scrapy.spidermiddlewares import httperror

import twisted.internet.error as internet_err
import twisted.web._newclient as newclient_err

from config import ProxyModel
from tddc import CacheManager, ExternManager, TaskRecordManager, DBSession

from worker.extern_modules.request import RequestExtra, FormRequestExtra
from worker.extern_modules.response import ResponseExtra

log = logging.getLogger(__name__)


task_conf = DBSession.query(ProxyModel).get(1)


class SingleSpider(scrapy.Spider):
    '''
    single spider
    '''

    SIGNAL_CRAWL_SUCCESSED = object()

    SIGNAL_CRAWL_FAILED = object()

    name = 'SingleSpider'

    start_urls = []

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(SingleSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.signal_dispatcher, signals.spider_opened)
        crawler.signals.connect(spider.signal_dispatcher, signals.spider_idle)
        crawler.signals.connect(spider.signal_dispatcher, signals.spider_error)
        return spider

    def __init__(self, callback=None):
        '''
        params[0]: 信号回调函数
        '''
        super(SingleSpider, self).__init__()
        self.signals_callback = callback

    def signal_dispatcher(self, signal):
        '''
        callback signal
        '''
        if self.signals_callback:
            if signal == signals.spider_idle or signal == signals.spider_error:
                raise DontCloseSpider('..I prefer live spiders.')
            elif signal == signals.spider_opened:
                self.signals_callback(signal, spider=self)

    def add_task(self, task, is_retry=False, times=1):
        """
        忘Spider队列里加入任务
        :param task:
        :param is_retry: 是否需要重试
        :param times: 重试次数
        :return:
        """
        if not is_retry:
            log.debug('Add New Task: ' + task.url)
        request_cls = ExternManager().get_model(task.platform, task.feature + '.request')
        if not request_cls:
            if not task.method or task.method == 'GET':
                request_cls = RequestExtra
            elif task.method == 'POST':
                request_cls = FormRequestExtra
            else:
                fmt = '[%s:%s] Invalid Task.'
                log.warning(fmt % (task.platform, task.id))
                return
        req = request_cls(self, task, times)
        self.crawler.engine.schedule(req, self)
        TaskRecordManager().start_task_timer(task)

    def http_error(self, task, times, proxy, response):
        status = response.value.response.status
        if status >= 500 or status in [408, 429]:
            fmt = '[%s:%s] Crawled Failed(> %d | %s <). Will Retry After While.'
            log.warning(fmt % (task.platform, task.url, status, proxy))
            self.add_task(task, True)
            return
        elif status == 404:
            retry_times = task.retry if task.retry else 3
            if times >= retry_times:
                fmt = '[%s:%s] Crawled Failed(> 404 | %s <). Not Retry.'
                log.warning(fmt % (task.platform,  task.url, proxy))
                if not self.signals_callback:
                    return
                self.signals_callback(self.SIGNAL_CRAWL_FAILED, task=task, status=status)
                return
            fmt = '[%s:%s] Crawled Failed(> %d | %s <). Will Retry After While.'
            log.warning(fmt % (task.platform, task.url, status, proxy))
            self.add_task(task, True, times + 1)
            return
        elif status == -1000:
            from worker.spider_manager import Crawler
            log.warning('[%s] Was No Proxy.' % task.platform)

            def _retry():
                self.add_task(task, True)
                Crawler().suspend_task_count -= 1
            gevent.spawn_later(5, _retry)
            Crawler().suspend_task_count += 1
            return
        else:
            err_msg = '{status}'.format(status=status)
            fmt = '[%s:%s] Crawled Failed(> %s | %s <). Will Retry After While.'
            log.warning(fmt % (task.platform, task.url, err_msg, proxy))
            self.remove_proxy(task, proxy)

    def remove_proxy(self, task, proxy):
        """
        从代理缓存池中移除当前 proxy
        :param task:
        :param proxy:
        :return:
        """
        if not proxy:
            return
        proxy = proxy.split('//')[1]
        if task.proxy == 'ADSL':
            CacheManager().remove('tddc:proxy:adsl', proxy)
        else:
            CacheManager().remove('%s:%s' % (task_conf.pool_key,
                                             task.platform),
                                  proxy)

    def error_back(self, response):
        task, times = response.request.meta['item']
        proxy = response.request.meta.get('proxy', None)
        if response.type == httperror.HttpError:
            self.http_error(task, times, proxy, response)
            return
        elif response.type == internet_err.TimeoutError:
            retry_times = task.retry if task.retry else 2
            fmt = '[%s:%s] Crawled Failed(> TimeoutError | %s <). Will Retry After While.'
            log.warning(fmt % (task.platform, task.url, proxy))
            if times >= retry_times:
                self.add_task(task, True)
                self.remove_proxy(task, proxy)
                return
            self.add_task(task, True, times + 1)
            return
        elif response.type in [internet_err.ConnectionRefusedError,
                               internet_err.TCPTimedOutError]:
            err_msg = '%d:%s' % (response.value.osError, response.value.message)
            self.remove_proxy(task, proxy)
        elif response.type == newclient_err.ResponseNeverReceived:
            err_msg = 'ResponseNeverReceived'
        else:
            err_msg = '%s' % response.value
        fmt = '[%s:%s] Crawled Failed(> %s | %s <). Will Retry After While.'
        log.warning(fmt % (task.platform, task.url, err_msg, proxy))
        self.add_task(task, True, times)

    def parse(self, response):
        task, times = response.request.meta.get('item')
        proxy = response.request.meta.get('proxy', None)
        response_cls = ExternManager().get_model(task.platform, task.feature + '.response')
        if not response_cls:
            response_cls = ResponseExtra
        rsp = response_cls(self, response)
        success = rsp.success()
        if success == -1:
            self.remove_proxy(task, proxy)
            fmt = '[%s:%s] Crawled Failed. Response Body Exception(%s).'
            log.warning(fmt % (task.platform, task.url, proxy))
            task.proxy = None
            self.add_task(task, True, times)
            return
        elif success == 0:
            self.add_task(task, True, times - 1)
            return
        if proxy and task.proxy and task.proxy != 'ADSL':
            def _back_pool():
                CacheManager().set('%s:%s' % (task_conf.pool_key,
                                              task.platform),
                                   proxy.split('//')[1])
            gevent.spawn_later(random.uniform(3, 5), _back_pool)
        if not self.signals_callback:
            return
        data = response.body
        self.signals_callback(SingleSpider.SIGNAL_CRAWL_SUCCESSED, task=task, data=data)
