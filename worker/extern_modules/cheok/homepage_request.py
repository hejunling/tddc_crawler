# -*- coding:utf-8 -*-
'''
Created on 2015年12月28日

@author: chenyitao
'''

from worker.extern_modules.request import RequestExtra


class CheokHomepageRequest(RequestExtra):

    platform = 'cheok'

    feature = 'cheok.buycar.request'

    version = '12345678'

    valid = '1'
