# -*- coding:utf-8 -*-
'''
Created on 2015年8月26日

@author: chenyitao
'''
from string import lower
from scrapy.http import Response

from config import ProxyModel
from tddc import CacheManager, DBSession

SWITCHING = False


class ProxyMiddleware(object):
    '''
    Proxy
    '''

    ADSL_PROXY = None

    proxy_conf = DBSession.query(ProxyModel).get(1)

    def process_request(self, request, spider):
        '''
        process request
        '''
        proxy = request.meta.get('proxy')
        if not proxy:
            task, _ = request.meta.get('item')
            if getattr(task, 'proxy', 'http') != 'None':
                if getattr(task, 'proxy', None) not in ['http', 'https', 'HTTP', 'HTTPS']:
                    request.meta['proxy'] = task.proxy
                    return
                if getattr(task, 'proxy', 'http') == 'ADSL':
                    ip_port = CacheManager().get_random('tddc:proxy:adsl', False)
                    # auth = base64.encodestring('tddc_crawler:tddc_crawler!@#$%^')
                    # request.headers['Proxy-Authorization'] = 'Basic ' + auth
                else:
                    ip_port = CacheManager().get_random('%s:%s' % (self.proxy_conf.pool_key,
                                                                   task.platform))
                    if ip_port:
                        request.headers['X-Forwarded-For'] = ip_port.split(':')[0]
                if not ip_port:
                    return Response(url=request.url, status=-1000, request=request)
                ip, port = ip_port.split(':')
                proxy = '{}://{}:{}'.format(lower(getattr(task, 'proxy_type', 'http')), ip, port)
                request.meta['proxy'] = proxy
