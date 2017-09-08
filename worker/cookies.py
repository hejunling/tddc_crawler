# -*- coding: utf-8 -*-
'''
Created on 2017年5月19日

@author: chenyitao
'''


import random

from tddc.base import EventCenter
from tddc.base.plugins import RedisClient

from crawler_site import CrawlerSite

from worker.common.event import EventType
from worker.common.queues import CrawlerQueues


class CookiesManager(RedisClient):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        super(CookiesManager, self).__init__(CrawlerSite.REDIS_NODES)
        EventCenter().register(EventType.Crawler.COOKIES, self._update_cookie)

    def _update_cookie(self, event):
        info = event.detail
        platform = info.get('platform')
        if not platform:
            return
        cookies = self.hget(CrawlerSite.COOKIES_HSET, platform)
        CrawlerQueues.PLATFORM_COOKIES[platform] = cookies

    @staticmethod
    def get_cookie(platform):
        cookies = CrawlerQueues.PLATFORM_COOKIES.get(platform)
        return random.choice(cookies) if cookies else None 

        
def main():
    pass

if __name__ == '__main__':
    main()
