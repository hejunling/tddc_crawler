# -*- coding: utf-8 -*-
'''
Created on 2017年9月6日

@author: chenyitao
'''

from tddc.common.models.events_model.event_base import EventBase


class EventType(object):

    NONE = None

    class Crawler(object):
    
        BASE_DATA = 1001
        
        COOKIES = 1002
        
        MODULE = 1003


class CrawlerCookiesEvent(EventBase):

    event_type = EventType.Crawler.COOKIES


class CrawlerModuleEvent(EventBase):
    
    event_type = EventType.Crawler.MODULE


class CrawlerBaseDataEvent(EventBase):

    event_type = EventType.Crawler.BASE_DATA

