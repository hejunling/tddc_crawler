# -*- coding: utf-8 -*-
'''
Created on 2017年4月14日

@author: chenyitao
'''
import gevent
from tddc import (KeepAliveConsumer, StatusManager, Singleton,
                  ConfigCenter, KeepAliveProducer, object2json, Storager)

from config import ConfigCenterExtern


class TaskStatus(object):
    CrawlTopic = 0

    WaitCrawl = 1
    CrawledSuccess = 200
    # CrawledFailed : 错误码为HTTP Response Status

    WaitParse = 1001
    ParseModuleNotFound = 1100
    ParsedSuccess = 1200
    ParsedFailed = 1400


class TaskManager(KeepAliveConsumer):
    '''
    classdocs
    '''
    __metaclass__ = Singleton
    _task_status_base_key_fmt = 'tddc:task:status:{platform}'

    def __init__(self):
        '''
        Constructor
        '''
        self.task_conf = ConfigCenterExtern().get_task()
        kafka_info = ConfigCenter().get_services('kafka')
        if not kafka_info:
            self.error('Kafka Server Info Not Found.')
            return
        kafka_nodes = ','.join(['%s:%s' % (info.host, info.port) for info in kafka_info['kafka']])
        super(TaskManager, self).__init__(self.task_conf.consumer_topic,
                                          self.task_conf.consumer_group,
                                          self.task_conf.local_task_queue_size,
                                          bootstrap_servers=kafka_nodes)
        self.info('Task Manager Is Starting.')
        self._totals = 0
        self._minutes = 0
        self._success = 0
        self._one_minute_past_success = 0
        self._failed = 0
        self._one_minute_past_failed = 0
        gevent.spawn(self._counter)
        gevent.sleep()
        self.info('Task Manager Was Ready.')

    def _counter(self):
        fmt = ('\n'
               '********* Task Status *********\n'
               '-> Totals: %d\n'
               '-> Average: %d\n'
               '-> Success: %d\n'
               '-> OneMinutePastSuccess: %d\n'
               '-> Failed: %d\n'
               '-> OneMinutePastFailed: %d\n'
               '*******************************\n')
        one_minute_past_status = tuple()
        while True:
            gevent.sleep(60)
            current_status = (self._totals,
                              self._success,
                              self._failed)
            if one_minute_past_status == current_status:
                continue
            one_minute_past_status = current_status
            self._minutes += 1
            self.info(fmt % (self._totals,
                             (self._success + self._failed) / (self._minutes if self._minutes != 0 else 1),
                             self._success,
                             self._one_minute_past_success,
                             self._failed,
                             self._one_minute_past_failed))
            self._one_minute_past_success = 0
            self._one_minute_past_failed = 0

    def _record_fetched(self, item):
        task = item
        if not hasattr(task, 'id'):
            return
        self._task_status_changed(task)
        self._totals += 1

    def _deserialization(self, item):
        class Task(object):
            cur_status = None
            pre_status = None
        return type('TaskRecord', (Task,), item)

    def get(self, block=True, timeout=None):
        task = super(TaskManager, self).get(block, timeout)
        return task

    def _task_status_changed(self, task):
        StatusManager().update_status(self._task_status_base_key_fmt.format(platform=task.platform),
                                      task.id,
                                      task.cur_status,
                                      task.pre_status if task.pre_status != task.cur_status else None)

    def task_successed(self, task, data):
        self._success += 1
        self._one_minute_past_success += 1
        if data:
            def _storaged(_):
                self.debug('[%s:%s] Storaged.' % (task.platform,
                                                  task.id))
                if task.cur_status != TaskStatus.CrawledSuccess:
                    self.debug('[%s:%s:%s] Task Success.' % (task.platform,
                                                             task.id,
                                                             task.url))
                    self._task_status_changed(task)
                    return

                def _push_task_to_parse(_):
                    self.debug('[%s:%s] Pushed(Topic:%s).' % (task.platform,
                                                              task.id,
                                                              self.task_conf.producer_topic))
                    self.debug('[%s:%s:%s] Task Success.' % (task.platform,
                                                             task.id,
                                                             task.url))
                    self._task_status_changed(task)

                KeepAliveProducer().push(self.task_conf.producer_topic,
                                         object2json(task),
                                         _push_task_to_parse)

            Storager().storage(data, _storaged)
        else:
            self.debug('[%s:%s:%s] Task Success.' % (task.platform,
                                                     task.id,
                                                     task.url))
            self._task_status_changed(task)

    def task_failed(self, task):
        self._failed += 1
        self._one_minute_past_failed += 1
        self._task_status_changed(task)
        self.warning('[%s:%s:%s] Task Failed(%d).' % (task.platform,
                                                      task.id,
                                                      task.url,
                                                      task.cur_status))

    def push_task(self, task, topic):
        def _pushed(_):
            self._task_status_changed(task)
        KeepAliveProducer().push(topic,
                                 object2json(task),
                                 _pushed)
