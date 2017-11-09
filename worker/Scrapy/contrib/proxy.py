# -*- coding:utf-8 -*-
'''
Created on 2015年8月26日

@author: chenyitao
'''

from scrapy.http import Response
from tddc import CacheManager

from config import ConfigCenterExtern


class ProxyMiddleware(object):
    '''
    Proxy
    '''

    def process_request(self, request, spider):
        '''
        process request
        '''
        proxy = request.meta.get('proxy')
        if not proxy:
            task, _ = request.meta.get('item')
            if getattr(task, 'proxy_type', 'http') != 'None':
                ip_port = CacheManager().get_random('%s:%s' % (ConfigCenterExtern().get_proxies().pool_key,
                                                               task.platform))
                if not ip_port:
                    return Response(url=request.url, status=-1000, request=request)
                ip, port = ip_port.split(':')
                proxy = '%s://%s:%s' % (getattr(task, 'proxy_type', 'http'), ip, port)
                request.meta['proxy'] = proxy
                request.headers['X-Forwarded-For'] = '8.8.8.8'
