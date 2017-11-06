# -*- coding: utf-8 -*-
'''
Created on 2017年9月6日

@author: chenyitao
'''

from tddc.common.models.exception.base import ExceptionModelBase

from crawler_site import CrawlerSite


class ExceptionType(object):

    class Crawler(object):
        CLIENT = 1101
        TASK_FAILED = 1201
        STORAGE_FAILED = 1301
        STORAGER_EXCEPTION = 1302
        PROXY = 1401
        NO_COOKIES = 1501
        COOKIES_INVALIDATE = 1502


class CrawlerClientException(ExceptionModelBase):

    EXCEPTION_TYPE = ExceptionType.Crawler.CLIENT

    @staticmethod
    def members():
        return dict(ExceptionModelBase.members(),
                    **{'client_id': CrawlerSite.CLIENT_ID})


class CrawlerTaskFailedException(ExceptionModelBase):

    EXCEPTION_TYPE = ExceptionType.Crawler.TASK_FAILED

    @staticmethod
    def members():
        return dict(ExceptionModelBase.members(),
                    **{'platform': None,
                       'task_id': None})


class CrawlerSrorageFailedException(ExceptionModelBase):

    EXCEPTION_TYPE = ExceptionType.Crawler.STORAGE_FAILED


class CrawlerStoragerException(ExceptionModelBase):

    EXCEPTION_TYPE = ExceptionType.Crawler.STORAGER_EXCEPTION


class CrawlerProxyException(ExceptionModelBase):

    EXCEPTION_TYPE = ExceptionType.Crawler.PROXY


class CrawlerNoCookiesException(ExceptionModelBase):

    EXCEPTION_TYPE = ExceptionType.Crawler.NO_COOKIES


class CrawlerCookiesInvalidateException(ExceptionModelBase):

    EXCEPTION_TYPE = ExceptionType.Crawler.COOKIES_INVALIDATE
