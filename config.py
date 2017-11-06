# -*- coding: utf-8 -*-
"""
Created on 2017年8月31日

@author: chenyitao
"""


class ConfigCenter(ConfigBase):

    @staticmethod
    def tables():
        return dict(ConfigBase.tables(),
                    **{'cookies': {'key': 'TEXT'},
                       'proxies': {'key': 'TEXT'},
                       'task': {'consumer_topic': 'TEXT',
                                'consumer_group': 'TEXT',
                                'producer_topic': 'TEXT',
                                'producer_group': 'TEXT',
                                'status_key_base': 'TEXT',
                                'record_key_base': 'TEXT',
                                'local_task_queue_size': 'TEXT'}})

    def get_cookies(self):
        return self._get_info('cookies')

    def get_proxies(self):
        return self._get_info('proxies')

    def get_task(self):
        return self._get_info('task')
