# -*- coding: utf-8 -*-
'''
Created on 2017年4月14日

@author: chenyitao
'''

import random
import threading
import time

import gevent
from tddc.base.plugins import RedisClient
from tddc.common import TDDCLogging

from crawler_site import CrawlerSite

from worker.common.queues import CrawlerQueues


class IPPool(RedisClient):
    pass


class CoolingQueue(object):
    
    def __init__(self):
        self.cur_timestamp = time.time()
        self._lock = threading.Lock()
        self._list = list()
        self._ips = list()
    
    def push(self, item):
        if self._lock.acquire():
            self._list.append({item: self.cur_timestamp})
            self._ips.append(item)
            self._lock.release()
        return True
    
    def pop(self, info):
        if self._lock.acquire():
            self._list.remove(info)
            self._ips.remove(info.keys()[0])
            self._lock.release()
    
    def qlist(self):
        return self._list

    def ips(self):
        return self._ips
    

class IPCoolingPoll(object):
    '''
    classdocs
    '''

    def __init__(self, cooldown=3):
        '''
        Constructor
        '''
        self._cur_timestamp = 0
        self._cooling_queue = CoolingQueue()
        self.cooldown = cooldown
        gevent.spawn(self.run)
        gevent.sleep()
    
    def push(self, item):
        self._cooling_queue.push(item)
    
    def ips(self):
        return set(self._cooling_queue.ips())
    
    def in_pool(self, item):
        return len(list(self.ips() & set([item])))
    
    def run(self):
        times = 0
        time_space = 0.5
        while True:
            gevent.sleep(time_space)
            self._cooling_queue.cur_timestamp += time_space
            if times % 10 == 0:
                self._cur_timestamp = time.time()
                self._cooling_queue.cur_timestamp = self._cur_timestamp
            times += 1
            ip_pool = self._cooling_queue.qlist()[:]
            if not len(ip_pool):
                continue
            self._cur_timestamp += time_space
            random_time = random.uniform(-1, 2)
            for i in range(0, len(ip_pool)):
                info = ip_pool[i]
                ip, platform = info.keys()[0]
                use_timestamp = info[(ip, platform)]
                if self._cur_timestamp - use_timestamp >= (self.cooldown) + random_time:
                    self._cooling_queue.pop(info)
                    CrawlerQueues.PLATFORM_PROXY.get(platform, set()).add(ip)


class CrawlProxyPool(object):
    '''
    classdocs
    '''
    
    IP_COOLING_POOL = IPCoolingPoll()

    def __init__(self):
        '''
        Constructor
        '''
        TDDCLogging.info('-->Crawl Proxy Pool Is Starting.')
        self._ip_pool = IPPool(CrawlerSite.REDIS_NODES)
        self._init_proxy()
        gevent.spawn(self._subscribe)
        gevent.sleep()
        gevent.spawn(self._proxy_unuseful_feedback)
        gevent.sleep()
        TDDCLogging.info('-->Crawl Proxy Pool Was Ready.')

    @staticmethod
    def get_proxy(platform):
        for _ in range(3):
            if not CrawlerQueues.PLATFORM_PROXY.get(platform):
                gevent.sleep(0.5)
            else:
                if len(CrawlerQueues.PLATFORM_PROXY.get(platform)):
                    break
        else:
            return None
        proxies = CrawlerQueues.PLATFORM_PROXY.get(platform)
        proxy = proxies.pop()
        while CrawlProxyPool.IP_COOLING_POOL.in_pool((proxy, platform)):
            if len(proxies):
                proxy = proxies.pop()
            else:
                return None
        CrawlProxyPool.IP_COOLING_POOL.push((proxy, platform))
        return proxy

    @staticmethod
    def get_random_proxy():
        for _, proxies in CrawlerQueues.PLATFORM_PROXY.items():
            return random.choice(list(proxies))
    
    def _init_proxy(self):
        s = self._ip_pool.scan_iter(CrawlerSite.PLATFORM_PROXY_SET_KEY_BASE + '*')
        for ret in s:
            key = ret.encode('utf-8')
            platform = key.split(':')[-1]
            ips = self._ip_pool.smembers(key)
            if not CrawlerQueues.PLATFORM_PROXY.get(platform):
                CrawlerQueues.PLATFORM_PROXY[platform] = set()
            CrawlerQueues.PLATFORM_PROXY[platform] |= set(ips)
    
    def _subscribe(self):
        items = self._ip_pool.psubscribe(CrawlerSite.PROXY_PUBSUB_PATTERN)
        for item in items:
            if item.get('type') == 'psubscribe':
                TDDCLogging.info('--->Subscribe: %s' % item.get('channel'))
                continue
            platform = item.get('channel', '').split(':')[-1]
            data = item.get('data')
            if not CrawlerQueues.PLATFORM_PROXY.get(platform):
                CrawlerQueues.PLATFORM_PROXY[platform] = set()
            CrawlerQueues.PLATFORM_PROXY[platform].add(data)
    
    def _proxy_unuseful_feedback(self):
        while True:
            platform, proxy = CrawlerQueues.UNUSEFUL_PROXY_FEEDBACK.get()
            if proxy in CrawlerQueues.PLATFORM_PROXY.get(platform, set()): 
                CrawlerQueues.PLATFORM_PROXY[platform].remove(proxy)
                self._ip_pool.srem(CrawlerSite.PLATFORM_PROXY_SET_KEY_BASE + platform,
                                   proxy.encode('utf-8'))


def main():
    import gevent.monkey
    gevent.monkey.patch_all()
    cpm = CrawlProxyPool()

    def test():
        while True:
            if CrawlerQueues.PLATFORM_PROXY.get('cheok'):
                ip = random.choice(list(CrawlerQueues.PLATFORM_PROXY['cheok']))
                CrawlerQueues.UNUSEFUL_PROXY_FEEDBACK.put(['cheok', ip])
            gevent.sleep(1)
    
    gevent.spawn(test)
    gevent.sleep()
    
    def publish(ip_pool, channel, publish_channel):
        for i in range(43):
            ip = '192.168.1.' + str(i)
            ip_pool.add(channel, ip)
            ip_pool._rdm.publish(publish_channel, ip)
            gevent.sleep(1)
    gevent.spawn(publish,
                 cpm._ip_pool,
                 CrawlerSite.PLATFORM_PROXY_SET_KEY_BASE + 'cheok',
                 CrawlerSite.PROXY_PUBSUB_PATTERN[:-1] + 'cheok')
    gevent.sleep()
    while True:
        gevent.sleep(60)
