# -*- coding: utf-8 -*-
"""
Created on 2017年8月31日

@author: chenyitao
"""

from tddc import WorkerConfigCenter


class ConfigCenterExtern(WorkerConfigCenter):

    @staticmethod
    def tables():
        return dict(WorkerConfigCenter.tables(),
                    **{'cookies': {'key': {"field_type": "TEXT",
                                           "default_value": "tddc:cookies"}},
                       'proxies': {'pool_key': {"field_type": "TEXT",
                                                "default_value": "tddc:proxy:pool"}}})

    def get_cookies(self):
        return self._get_info('cookies')

    def get_proxies(self):
        return self._get_info('proxies')
