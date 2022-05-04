# -*- coding: utf-8 -*-
import scrapy
from TenderCrab.items import TendercrabItem
from dateutil.parser import parse, ParserError
from scrapy.http import Response
import re

from TenderCrab.DataModels import get_url_hashset


class TendersdSpider(scrapy.Spider):
    name = 'TenderSD'
    url_hashset = set()
    # allowed_domain = ['ccgp-shandong.gov.cn']

    def __init__(self, pages=None, *args, **kwargs):
        super(TendersdSpider, self).__init__(*args, **kwargs)
        self.start_urls = ['http://ccgp-shandong.gov.cn/sdgp2017/site/listnew.jsp?grade=province&colcode=0302',
            'http://ccgp-shandong.gov.cn/sdgp2017/site/listnew.jsp?grade=city&colcode=0304']
        if pages:
            self.pages = int(pages)
        else:
            self.pages = None

        # 以下对数据库的内容进行更新
        if not self.url_hashset:
            self.url_hashset = get_url_hashset()
            self.logger.info("The url_hashset is updated.")

    def parse(self, response: Response):
        self.logger.debug(f'Current URL: {response.url}')
        # 抓取相关的标讯内容链接
        links = response.css('span.title span a')
        pubDates = response.css('span.hits')

        if len(links) == 0:
            yield
        if len(links) != len(pubDates):
            self.logger.debug('Links length and pubDates are not equal!')
            yield
                
        for link, pubDate in zip(links, pubDates):
            try:
                url = link.attrib['href']
                title = link.attrib['title']
                pubDate = pubDate.css('::text').get()
                
                url = response.urljoin(url)
                # 如果这个URL没的被抓取过
                if hash(url) not in self.url_hashset:
                    self.logger.info(f'Yield the tender pages: {url}')
                    yield response.follow(url, callback=self.parse_item, 
                            cb_kwargs={'title': title, 
                            'publishDate': pubDate
                            })
                else:
                    self.logger.debug(f'Skipping url: {url}')
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
            temp = response.css('#totalnum::text').get()
            if temp:
                totalpage = int(temp)
            else:
                totalpage = 1
            crawl_pages = self.pages if self.pages else totalpage
            if crawl_pages == 1:
                yield

            for i in range(curpage + 1, crawl_pages + 1):
                url = f'{base_url}?curpage={i}&colcode={colcode}&grade={grade}'
                self.logger.info(f'Starting... colcode: {colcode}, curpage: {i}')
                self.logger.debug(f'Yield URL: {url}')
                yield response.follow(url, self.parse)

    def parse_item(self, response, title, publishDate):
        self.logger.info(f'Parsing URL: {response.url}')
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