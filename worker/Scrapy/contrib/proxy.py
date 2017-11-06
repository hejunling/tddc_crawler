# -*- coding:utf-8 -*-
'''
Created on 2015年8月26日

@author: chenyitao
'''

from scrapy.http import Response

from ...proxy_pool import CrawlProxyPool


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
            if task.proxy_type != 'None':
                ip_port = CrawlProxyPool.get_proxy(task.platform)
                if not ip_port:
                    return Response(url=request.url, status=-1000, request=request)
                ip, port = ip_port.split(':')
                proxy = '%s://%s:%s' % (task.proxy_type if task.proxy_type else 'http', ip, port)
                request.meta['proxy'] = proxy
                # request.headers['X-Forwarded-For'] = '10.10.10.10'
                # request.headers['X-Real-IP'] = '10.10.10.10'
