# -*- coding: utf-8 -*-
'''
Created on 2017年4月14日

@author: chenyitao
'''

from tddc.base import TaskManagerBase
from tddc.common import TDDCLogging
from tddc.common.models import Task

from crawler_site import CrawlerSite
from worker.common.queues import CrawlerQueues


class CrawlTaskManager(TaskManagerBase):
    '''
    classdocs
    '''

    topics = {}

    def __init__(self):
        '''
        Constructor
        '''
        TDDCLogging.info('-->Task Manager Is Starting.')
        super(CrawlTaskManager, self).__init__(CrawlerSite, CrawlerQueues)
        TDDCLogging.info('-->Task Manager Was Ready.')

    def task_status_process(self, task):
        self.create_record(task)
        self.update_status(task, Task.Status.WAIT_CRAWL, Task.Status.CRAWL_TOPIC)

    def pushed(self, task):
        TDDCLogging.debug('[%s:%s] Crawled Successed.' % (task.platform,
                                                          task.row_key))

    def task_status_changed(self, task, new_status):
        if new_status != Task.Status.CRAWL_SUCCESS:
            return
        CrawlerQueues.TASK_OUTPUT.put(task)
