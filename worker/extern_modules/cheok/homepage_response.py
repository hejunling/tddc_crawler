# -*- coding:utf-8 -*-
'''
Created on 2015年12月28日

@author: chenyitao
'''

from worker.extern_modules.response import ResponseExtra


class CheokHomepageResponse(ResponseExtra):

    platform = 'cheok'

    feature = 'cheok.buycar.response'

    version = '123456789'

    def success(self):
        if not super(CheokHomepageResponse, self).success():
            return False
        return True
