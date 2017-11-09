# -*- coding:utf-8 -*-
'''
Created on 2015年12月28日

@author: chenyitao
'''
import random
import urlparse

import gevent
from scrapy import signals
import scrapy
from scrapy.exceptions import DontCloseSpider
from scrapy.http import Request, FormRequest
from scrapy.spidermiddlewares import httperror

import twisted.internet.error as internet_err
import twisted.web._newclient as newclient_err

from tddc import TDDCLogger, object2json, CacheManager

from config import ConfigCenterExtern


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

    @staticmethod
    def _init_request_headers(task):
        iheaders = {}
        if not task.headers:
            url_info = urlparse.urlparse(task.url)
            task.headers = {'Host': url_info[1]}
        for k, v in task.headers.items():
            if not v:
                if k == 'Host':
                    url_info = urlparse.urlparse(task.url)
                    iheaders[k] = url_info[1]
                continue
            iheaders[k] = v
        return iheaders

    def add_task(self, task, is_retry=False, times=1):
        if not is_retry:
            self.debug('Add New Task: ' + task.url)
        headers = self._init_request_headers(task)
        req = (self._make_get_request(task, headers, times)
               if getattr(task, 'method', 'GET') == 'GET'
               else self._make_post_request(task, headers, times))
        self.crawler.engine.schedule(req, self)

    def _make_get_request(self, task, headers, times):
        req = Request(task.url,
                      headers=headers,
                      cookies=getattr(task, 'cookie', None),  # or CookiesManager.get_cookie(task.platform),
                      callback=self.parse,
                      errback=self.error_back,
                      meta={'item': [task, times]},
                      dont_filter=True)
        return req

    def _make_post_request(self, task, headers, times):
        form_data = {'params': headers.get('post_params', None)}
        req = FormRequest(task.url,
                          formdata=form_data,
                          headers=headers,
                          cookies=task.cookie or CookiesManager.get_cookie(task.platform),
                          callback=self.parse,
                          errback=self.error_back,
                          meta={'item': [task, times]},
                          dont_filter=True)
        return req

    def error_back(self, response):
        task, times = response.request.meta['item']
        proxy = response.request.meta.get('proxy', None)
        if response.type == httperror.HttpError:
            status = response.value.response.status
            if status >= 500 or status in [408, 429]: 
                fmt = ('[%s:%s] Crawled Failed(> %d | %s <). '
                       'Will Retry After While.')
                self.warning(fmt % (task.platform,
                                    task.url,
                                    status,
                                    proxy))
                self.add_task(task, True)
                return
            elif status == 404:
                retry_times = task.retry if task.retry else 3
                if times >= retry_times:
                    fmt = ('[%s:%s] Crawled Failed(> 404 | %s <). '
                           'Not Retry.')
                    self.warning(fmt % (task.platform,
                                        task.url,
                                        proxy))
                    callable(self.signals_callback(self.SIGNAL_CRAWL_FAILED,
                                                   task=task,
                                                   status=status))
                    return
                fmt = ('[%s:%s] Crawled Failed(> %d | %s <). '
                       'Will Retry After While.')
                self.warning(fmt % (task.platform,
                                    task.url,
                                    status,
                                    proxy))
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
        elif response.type == internet_err.TimeoutError:
            err_msg = 'TimeoutError'
        elif response.type in [internet_err.ConnectionRefusedError,
                               internet_err.TCPTimedOutError]:
            err_msg = '%d:%s' % (response.value.osError, response.value.message)
        elif response.type == newclient_err.ResponseNeverReceived:
            err_msg = 'ResponseNeverReceived'
        else:
            err_msg = '%s' % response.value
        if proxy:
            proxy = proxy.split('//')[1]
            CacheManager().remove('%s:%s' % (ConfigCenterExtern().get_proxies().pool_key,
                                             task.platform),
                                  proxy)
        fmt = ('[%s:%s] Crawled Failed(> %s | %s <). '
               'Will Retry After While.')
        self.warning(fmt % (task.platform,
                            task.url,
                            err_msg,
                            proxy))
        self.add_task(task, True, times)

    def parse(self, response):
        task, _ = response.request.meta.get('item')
        proxy = response.request.meta.get('proxy', None)
        if proxy:
            def _back_pool():
                CacheManager().set('%s:%s' % (ConfigCenterExtern().get_proxies().pool_key,
                                              task.platform),
                                   proxy.split('//')[1])

            gevent.spawn_later(random.uniform(3, 5), _back_pool)
        # extern = Che300CrawlerExtern(task, response, self)
        if self.signals_callback:
            data = {'table': task.platform,
                    'row_key': task.row_key,
                    'data': {'source': {'rsp': '|'.join((response.url, str(response.status))),
                                        'content': response.body},
                             'task': {'task': object2json(task)}}}
            self.signals_callback(SingleSpider.SIGNAL_CRAWL_SUCCESSED,
                                  task=task,
                                  data=data)
