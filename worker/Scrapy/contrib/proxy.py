# -*- coding:utf-8 -*-
'''
Created on 2015年8月26日

@author: chenyitao
'''

from scrapy.http import Response
from tddc import CacheManager

from config import ConfigCenterExtern


SWITCHING = False


class ProxyMiddleware(object):
    '''
    Proxy
    '''

    ADSL_PROXY = None

    def process_request(self, request, spider):
        '''
        process request
        '''
        proxy = request.meta.get('proxy')
        if not proxy:
            task, _ = request.meta.get('item')
            if getattr(task, 'proxy_type', 'http') != 'None':
                if getattr(task, 'proxy_type', 'http') == 'ADSL':
                    ip_port = CacheManager().get_random('tddc:proxy:adsl', False)
                else:
                    ip_port = CacheManager().get_random('%s:%s' % (ConfigCenterExtern().get_proxies().pool_key,
                                                                   task.platform))
                    request.headers['X-Forwarded-For'] = ip_port.split(':')[0]
                if not ip_port:
                    return Response(url=request.url, status=-1000, request=request)
                ip, port = ip_port.split(':')
                proxy = 'http://%s:%s' % (ip, port)  # getattr(task, 'proxy_type', 'http'),
                request.meta['proxy'] = proxy
