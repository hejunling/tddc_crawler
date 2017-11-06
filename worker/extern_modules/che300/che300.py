# -*- coding: utf-8 -*-
'''
Created on 2017年5月19日

@author: chenyitao
'''

import hashlib
import re

import gevent
import time

import requests


class Che300CrawlerExtern(object):
    def __init__(self, *args, **kwargs):
        self._timeout = 30
        self._task = args[0]
        self._response = args[1]
        self._spider = args[2]
        self._process()

    def _process(self):
        proxy = self._response.request.meta.get('proxy')
        proxy = {'http': proxy}
        headers = self._response.request.headers
        headers = {k:v[0] for k,v in headers.items()}
        headers['Referer'] = self._task.url
        _che300_cookies = [cookie for cookie in self._response.headers.getlist('Set-Cookie')
                          if cookie[:7] == '_che300'][-1]
        _che300_name, _che300_cookie = _che300_cookies.split(';')[0].split('=')
        spidercookie_name, spidercode_name = re.findall('cookie="(.*?)="', self._response.body)
        spidercookie = str(int(time.time()))
        md5 = hashlib.md5()
        md5.update(spidercookie)
        spidercode = md5.hexdigest()
        spidercode = spidercode[16:] + spidercode[:16]
        self._task.cookie = {_che300_name: _che300_cookie,
                             spidercookie_name: spidercookie,
                             spidercode_name: spidercode}
        gevent.spawn(self._request, self._task.url, headers, self._task.cookie, proxy)
        gevent.sleep()

    def _request(self, url, headers, cookies, proxies):
        rsp = requests.get(url,
                           headers=headers,
                           cookies=cookies,
                           proxies=proxies)
        print(rsp)
        if 'trackEvent' in rsp.content:
            print('Success.')
        else:
            print('Failed.')
