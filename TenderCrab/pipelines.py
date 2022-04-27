# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

from TenderCrab.items import TendercrabItem
from TenderCrab.DataModels import TenderItem
import sqlalchemy as sa
import TenderCrab.settings as settings


class TendercrabPipeline(object):
    def __init__(self):
        engine = sa.create_engine(settings.DBURL)
        Session = sa.orm.sessionmaker()
        self.session = Session(bind=engine)

    def process_item(self, item, spider):
        if isinstance(item, TendercrabItem):
            dbItem = TenderItem()
            dbItem.name = item['name']
            dbItem.seller = item['seller']
            dbItem.seller_address = item['sellerAddress']
            dbItem.url = item['url']
            dbItem.publish_date = item['publishDate']
            dbItem.price = item['price']
            dbItem.body = item['body']
            self.session.add(dbItem)
            self.session.commit()
        return item
