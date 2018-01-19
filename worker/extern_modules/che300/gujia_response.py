# -*- coding:utf-8 -*-
'''
Created on 2015年12月28日

@author: chenyitao
'''

from worker.extern_modules.response import ResponseExtra


class Che300GujiaResponse(ResponseExtra):

    platform = 'che300'

    feature = 'che300.gujia.response'

    version = '1516329199'

    def success(self):
        if not super(Che300GujiaResponse, self).success():
            return False
        if self.response.body.find('spidercooskie') and self.response.body.find('spidercode'):
            task, times = self.response.request.meta['item']
            proxy = self.response.request.meta.get('proxy', None)
            task.proxy = proxy
            task.times = times
            task.cookies = ''
        return True
