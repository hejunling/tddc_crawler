# -*- coding: utf-8 -*-
'''
Created on 2015年12月28日

@author: chenyitao
'''

import urlparse

from scrapy.http import Request, FormRequest
from tddc import ExternBase


class HeadersHelper(object):
    """
    默认请求Headers
    """

    task = None

    request_headers = {'Accept': ('text/html,application/xhtml+xml,application/xml;'
                                  'q=0.9,image/webp,image/apng,*/*;q=0.8'),
                       'Accept-Encoding': 'gzip, deflate, br',
                       'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
                       'Cache-Control': 'max-age=0',
                       'Connection': 'keep-alive',
                       'DNT': '1',
                       'Upgrade-Insecure-Requests': '1'}

    def _headers(self):
        if not self.task:
            return self.request_headers
        url_info = urlparse.urlparse(self.task.url)
        self.request_headers['Host'] = url_info[1]
        if hasattr(self.task, 'referer'):
            self.request_headers['Referer'] = self.task.referer
        if hasattr(self.task, 'cookies'):
            # cookies = '; '.join(['%s=%s' % (k, v) for k, v in self.task.cookies.items()])
            cookies = '_che300=%s; spidercooskieXX12=%s; spidercodeCI12X3=%s' % (self.task.cookies.get('_che300'),
                                                                                 self.task.cookies.get('spidercooskieXX12'),
                                                                                 self.task.cookies.get('spidercodeCI12X3'))
            self.request_headers['Cookie'] = cookies
        return self.request_headers


class RequestExtra(Request, ExternBase, HeadersHelper):
    """
    GET 请求扩展
    """

    def __init__(self, spider=None, task=None, times=0, **kwargs):
        self.task = task
        if spider:
            super(RequestExtra, self).__init__(url=task.url,
                                               headers=self._headers(),
                                               callback=spider.parse,
                                               errback=spider.error_back,
                                               meta={'item': [task, times]},
                                               dont_filter=True,
                                               # cookies=getattr(task, 'cookies', None),
                                               **kwargs)
        else:
            super(RequestExtra, self).__init__(**kwargs)


class FormRequestExtra(FormRequest, ExternBase, HeadersHelper):
    """
    POST 请求扩展
    """

    def __init__(self, spider=None, task=None, times=0, **kwargs):
        self.task = task
        if spider:
            super(FormRequestExtra, self).__init__(url=task.url,
                                                   formdata=task.data,
                                                   headers=self._headers(),
                                                   callback=spider.parse,
                                                   errback=spider.error_back,
                                                   meta={'item': [task, times]},
                                                   dont_filter=True,
                                                   cookies=getattr(task, 'cookies', None),
                                                   **kwargs)
        else:
            super(FormRequestExtra, self).__init__(**kwargs)
