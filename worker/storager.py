# -*- coding: utf-8 -*-
'''
Created on 2017年4月14日

@author: chenyitao
'''

import gevent

from worker.common.queues import CrawlerQueues
from tddc.base import StoragerBase
from tddc.common.models.task import Task


class CrawlStorager(StoragerBase):
    '''
    classdocs
    '''
    
    FAMILY = 'source'

    def _push_success(self, task, storage_info):
        CrawlerQueues.TASK_STATUS.put((task,
                                       storage_info.get('rsp')[1] if storage_info.get('rsp') else None,
                                       Task.Status.WAIT_CRAWL))


def main():
    CrawlStorager()
    while True:
        gevent.sleep()

if __name__ == '__main__':
    main()
