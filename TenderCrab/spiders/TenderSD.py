# -*- coding: utf-8 -*-
import scrapy
from TenderCrab.items import TendercrabItem
from dateutil.parser import parse, ParserError
from scrapy.http import Response
import re
from sqlalchemy.orm import sessionmaker
import sqlalchemy as sa
import TenderCrab.settings as settings
from TenderCrab.DataModels import TenderItem, get_url_hashset


class TendersdSpider(scrapy.Spider):
    name = 'TenderSD'
    url_hashset = set()
    engine = sa.create_engine(settings.DBURL)
    Session = sessionmaker(bind=engine)    
    
    def __init__(self, pages=None, *args, **kwargs):
        super(TendersdSpider, self).__init__(*args, **kwargs)
        self.start_urls = ['http://ccgp-shandong.gov.cn/sdgp2017/site/listnew.jsp?grade=province&colcode=0302',
            'http://ccgp-shandong.gov.cn/sdgp2017/site/listnew.jsp?grade=city&colcode=0304']
        if pages:
            self.pages = int(pages)
        else:
            self.pages = None

        # 以下对数据库的内容进行更新
        if self.url_hashset:
            return        
        with self.Session() as session:
            self.url_hashset = get_url_hashset()
 

    def parse(self, response: Response):        
        self.logger.debug(f'Current URL: {response.url}')
        # 抓取相关的标讯内容链接
        links = response.css('span.title span a')
        pubDates = response.css('span.hits')

        if len(links) == 0:
            yield
        if len(links) != len(pubDates):
            yield
                
        for link, pubDate in zip(links, pubDates):
            try:
                url = link.css('::attr("href")').extract()[0]
                title = link.css('::attr("title")').extract()[0]
                pubDate = pubDate.css('::text').extract()[0]
                
                url = response.urljoin(url)
                # 如果已经抓取过了，则更新title
                if hash(url) in self.url_hashset:
                    item = TendercrabItem()
                    item['url'] = url
                    item['title'] = title
                    try:
                        item['publishDate'] = parse(pubDate)
                    except ParserError:
                        item['publishDate'] = None
                        self.logger.info(f'Error to parse publishDate: {pubDate}')                    
                    yield item
                else:
                    self.logger.debug(f'Yield the tender pages: {url}')
                    yield response.follow(url, callback=self.parse_item, 
                            cb_kwargs={'title': title, 
                            'publishDate': pubDate
                            })
            except IndexError:
                self.logger.debug('Failed to extract url from span.')

        base_url = response.url.split('?')[0]
        # 得到colcode值，0302为省级，0304为市县
        colcode = re.findall(r'colcode=(\d+)', response.url)[0]
        grade = re.findall(r'grade=(\w+)', response.url)[0]
        # 得到curpage值，默认是1
        temp = re.findall(r'curpage=(\d+)', response.url)

        if temp:
            curpage = temp[0]
        else:
            curpage = 1
       
        self.logger.debug(f'The URL of parse() is: {response.url}')

        # 首先将所有的页面都排到队列里
        if curpage == 1:
            temp = response.css('#totalnum::text').getall()
            if temp:
                totalpage = int(temp[0])
            else:
                totalpage = 1
            crawl_pages = self.pages if self.pages else totalpage
            if crawl_pages ==1:
                yield

            for i in range(curpage + 1, crawl_pages + 1):
                url = f'{base_url}?curpage={i}&colcode={colcode}&grade={grade}'
                self.logger.info(f'Starting... colcode: {colcode}, curpage: {i}')
                self.logger.debug(f'Yield URL: {url}')
                yield response.follow(url, self.parse)


    def parse_item(self, response, title, publishDate):
        # self.logger.debug(f'Parsing URL: {response.url}')
        item = TendercrabItem()
        item['url'] = response.url
        item['title'] = title
        try:
            item['publishDate'] = parse(publishDate)
        except ParserError:
            self.logger.info(f'Error to parse publishDate: {publishDate}')
        body = response.css('div#textarea').get()
        item['body'] = body
        item['name'] = ''
        item['sellerAddress'] = ''
        item['price'] = None
        item['seller'] = ''
        yield item
        

