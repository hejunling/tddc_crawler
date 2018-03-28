# -*- coding:utf-8 -*-
'''
Created on 2015年12月28日

@author: chenyitao
'''

import hashlib
import re

from worker.extern_modules.response import ResponseExtra


class Che300GujiaResponse(ResponseExtra):

    platform = 'che300'

    feature = 'che300.gujia.response'

    version = '1516329199'

    def success(self):
        if not super(Che300GujiaResponse, self).success():
            return -1
        if self.response.body.find('spidercooskie') > -1 and self.response.body.find('spidercode') > -1:
            task, times = self.response.request.meta['item']
            proxy = self.response.request.meta.get('proxy', None)
            task.proxy = proxy
            task.referer = self.response.url
            task.times = times
            timestamp = re.search('window.location.href,t="(.*?)",', self.response.body).groups()[0]
            url = self.response.url[:self.response.url.find('rt=')]
            url += ('rt=%s924' % timestamp)
            task.url = url
            spidercooskie, spidercode = re.findall('document.cookie="(.*?)="', self.response.body)
            _m = hashlib.md5()
            _m.update(timestamp)
            code = _m.hexdigest()
            code = code[16:] + code[:16]
            set_cookie = [cookie for cookie in self.response.headers.getlist('Set-Cookie')
                          if '_che300' in cookie][-1].split(';')[0].split('=')[1]
            task.cookies = {'_che300': set_cookie,
                            spidercooskie: timestamp,
                            spidercode: code}
            return 0
        elif self.response.body.find('name="code"') > -1:
            return -1
        return 1
