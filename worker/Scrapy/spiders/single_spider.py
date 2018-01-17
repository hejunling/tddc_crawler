# -*- coding:utf-8 -*-
'''
Created on 2015年12月28日

@author: chenyitao
'''

import random

import gevent.queue
from scrapy import signals
import scrapy
from scrapy.exceptions import DontCloseSpider
from scrapy.spidermiddlewares import httperror

import twisted.internet.error as internet_err
import twisted.web._newclient as newclient_err

from tddc import TDDCLogger, object2json, CacheManager, TaskManager, ExternManager

from config import ConfigCenterExtern
from worker.extern_modules.request import RequestExtra, FormRequestExtra
from worker.extern_modules.response import ResponseExtra


class SingleSpider(scrapy.Spider, TDDCLogger):
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
        params[0]:callback 
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
        if not is_retry:
            self.debug('Add New Task: ' + task.url)
        request_cls = ExternManager().get_model(task.platform, task.feature + '.request')
        if not request_cls:
            method = getattr(task, 'method', 'GET')
            if method == 'GET':
                request_cls = RequestExtra
            elif method == 'POST':
                request_cls = FormRequestExtra
            else:
                fmt = '[%s:%s] Invalid Task.'
                self.warning(fmt % (task.platform, task.id))
                return
        req = request_cls(self, task, times)
        self.crawler.engine.schedule(req, self)
        TaskManager().task_status_changed(task)

    def http_error(self, task, times, proxy, response):
        status = response.value.response.status
        if status >= 500 or status in [408, 429]:
            fmt = '[%s:%s] Crawled Failed(> %d | %s <). Will Retry After While.'
            self.warning(fmt % (task.platform, task.url, status, proxy))
            self.add_task(task, True)
            return
        elif status == 404:
            retry_times = task.retry if task.retry else 3
            if times >= retry_times:
                fmt = '[%s:%s] Crawled Failed(> 404 | %s <). Not Retry.'
                self.warning(fmt % (task.platform,  task.url, proxy))
                if not self.signals_callback:
                    return
                self.signals_callback(self.SIGNAL_CRAWL_FAILED, task=task, status=status)
                return
            fmt = '[%s:%s] Crawled Failed(> %d | %s <). Will Retry After While.'
            self.warning(fmt % (task.platform, task.url, status, proxy))
            self.add_task(task, True, times + 1)
            return
        elif status == -1000:
            self.warning('[%s] Was No Proxy.' % task.platform)

            def _retry():
                self.add_task(task, True)
            gevent.spawn_later(5, _retry)
            return
        else:
            err_msg = '{status}'.format(status=status)
            fmt = '[%s:%s] Crawled Failed(> %s | %s <). Will Retry After While.'
            self.warning(fmt % (task.platform, task.url, err_msg, proxy))
            self.remove_proxy(task, proxy)

    def remove_proxy(self, task, proxy):
        if not proxy:
            return
        proxy = proxy.split('//')[1]
        if getattr(task, 'proxy_type', 'http') == 'ADSL':
            CacheManager().remove('tddc:proxy:adsl', proxy)
        else:
            CacheManager().remove('%s:%s' % (ConfigCenterExtern().get_proxies().pool_key,
                                             task.platform),
                                  proxy)

    def error_back(self, response):
        task, times = response.request.meta['item']
        proxy = response.request.meta.get('proxy', None)
        if response.type == httperror.HttpError:
            self.http_error(task, times, proxy, response)
            return
        elif response.type == internet_err.TimeoutError:
            err_msg = 'TimeoutError'
        elif response.type in [internet_err.ConnectionRefusedError,
                               internet_err.TCPTimedOutError]:
            err_msg = '%d:%s' % (response.value.osError, response.value.message)
            self.remove_proxy(task, proxy)
        elif response.type == newclient_err.ResponseNeverReceived:
            err_msg = 'ResponseNeverReceived'
        else:
            err_msg = '%s' % response.value
        fmt = '[%s:%s] Crawled Failed(> %s | %s <). Will Retry After While.'
        self.warning(fmt % (task.platform, task.url, err_msg, proxy))
        self.add_task(task, True, times)

    def parse(self, response):
        task, times = response.request.meta.get('item')
        proxy = response.request.meta.get('proxy', None)
        response_cls = ExternManager().get_model(task.platform, task.feature + '.response')
        if not response_cls:
            response_cls = ResponseExtra
        if not response_cls(self, response).success():
            self.remove_proxy(task, proxy)
            fmt = '[%s:%s] Crawled Failed. Response Body Exception(%s).'
            self.warning(fmt % (task.platform, task.url, proxy))
            self.add_task(task, True, times)
            return
        if getattr(task, 'proxy_type', 'http') != 'ADSL':
            def _back_pool():
                CacheManager().set('%s:%s' % (ConfigCenterExtern().get_proxies().pool_key,
                                              task.platform),
                                   proxy.split('//')[1])
            gevent.spawn_later(random.uniform(3, 5), _back_pool)
        if not self.signals_callback:
            return
        data = {'table': task.platform,
                'row_key': task.row_key,
                'data': {'source': {'rsp': '|'.join((response.url, str(response.status))),
                                    'content': response.body},
                         'task': {'task': object2json(task)}}}
        self.signals_callback(SingleSpider.SIGNAL_CRAWL_SUCCESSED, task=task, data=data)
