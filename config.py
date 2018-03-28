# -*- coding: utf-8 -*-
"""
Created on 2017年8月31日

@author: chenyitao
"""
from sqlalchemy import Column, Integer, String

from tddc import Base, engine


class ProxyModel(Base):
    __tablename__ = 'proxy_info'

    id = Column(Integer, primary_key=True)
    source_key = Column(String(32))
    pool_key = Column(String(32))


Base.metadata.create_all(engine)
