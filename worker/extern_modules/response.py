# -*- coding: utf-8 -*-
'''
Created on 2015年12月28日

@author: chenyitao
'''

from tddc import ExternBase


class ResponseExtra(ExternBase):
    """
    Response扩展
    """

    def __init__(self, spider, response):
        self.spider = spider
        self.response = response
        super(ResponseExtra, self).__init__()

    def success(self):
        return len(self.response.body)
