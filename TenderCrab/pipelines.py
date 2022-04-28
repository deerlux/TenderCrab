# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

from TenderCrab.items import TendercrabItem
from TenderCrab.DataModels import TenderItem
import TenderCrab.DataModels as DataModels
import sqlalchemy as sa
import TenderCrab.settings as settings

class TendercrabPipeline(object):
    
    def __init__(self):
        
        engine = sa.create_engine(settings.DBURL)        
        self.session = DataModels.Session()

    def process_item(self, item, spider):
        if isinstance(item, TendercrabItem):
            dbItem = TenderItem()
            dbItem.url = item['url']
            dbItem.publish_date = item['publishDate']
            dbItem.title = item['title']
            
            try:
                dbItem.body = item['body']
            except KeyError:
                stmt = sa.update(TenderItem).where(TenderItem.url==item['url']).values(title=item['title'])
                self.session.execute(stmt)
                self.session.commit()
                spider.logger.debug(f'The tile is updated:{item["url"]} : {item["title"]}')
                return item
            
            dbItem.name = item['name']
            dbItem.seller = item['seller']
            dbItem.seller_address = item['sellerAddress']
                   
            dbItem.price = item['price']
            
            self.session.add(dbItem)
            self.session.commit()
            spider.logger.debug(f'The data is inserted: {item["url"]}')
        return item
