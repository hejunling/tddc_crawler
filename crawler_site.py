# -*- coding: utf-8 -*-
'''
Created on 2017年6月15日

@author: chenyitao
'''

from tddc import conf

from worker.common import event
from worker.common.event import EventType


class CrawlerSite(conf.SiteBase):

    WORKER_NAME = 'Crawler'
    
    EVENT_TOPIC = 'tddc_c_event'
    
    # Crawler Concurrent
    CONCURRENT = 100

    # Crawler Topic Group
    CRAWL_TOPIC_GROUP = 'tddc.crawler'

    EVENT_TABLES = {EventType.Crawler.BASE_DATA: event.CrawlerBaseDataEvent,
                    EventType.Crawler.COOKIES: event.CrawlerCookiesEvent,
                    EventType.Crawler.MODULE: event.CrawlerModuleEvent}
