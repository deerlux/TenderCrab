# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class TendercrabItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    name = scrapy.Field()
    title = scrapy.Field()
    url = scrapy.Field()
    body = scrapy.Field()
    publishDate = scrapy.Field()
    scopy = scrapy.Field()
    buyer = scrapy.Field()
    seller = scrapy.Field()
    price = scrapy.Field()
    sellerAddress = scrapy.Field()
    
