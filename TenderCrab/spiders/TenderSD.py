# -*- coding: utf-8 -*-
import scrapy
from TenderCrab.items import TendercrabItem
from dateutil.parser import parse, ParserError
from scrapy.http import Response
import re


class TendersdSpider(scrapy.Spider):
    name = 'TenderSD'
    
    def __init__(self, pages=None, *args, **kwargs):
        super(TendersdSpider, self).__init__(*args, **kwargs)
        self.start_urls = ['http://ccgp-shandong.gov.cn/sdgp2017/site/listnew.jsp?grade=province&colcode=0302',
            'http://ccgp-shandong.gov.cn/sdgp2017/site/listnew.jsp?grade=city&colcode=0304']
        if pages:
            self.pages = int(pages)
        else:
            self.pages = None
 

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
                self.logger.debug(f'Yield URL: {url}')
                yield response.follow(url, self.parse)


    def parse_item(self, response, title, publishDate):
        # self.logger.debug(f'Parsing URL: {response.url}')
        item = TendercrabItem()
        item['url'] = response.url
        try:
            item['title'] = response.xpath(r'//div[@align="center"]//text()').extract()[0].strip('\xa0')
        except IndexError as e:
            self.logger.error(e)
            self.logger.warn(f'The Error URL: {response.url}')
            yield None

        sels = response.xpath(r'//table[@id="NoticeDetail"]//tr')
        # 如果没有搜到，可能这个URL地址没有中标清单表
        if not sels:
            # 采用另外一种方式搜寻相关的数据
            temp = response.xpath('//td')
            tender_table = None
            for sel in temp:
                data = sel.xpath('text()').extract()
                if data:
                    if data[0].strip() == '标包':
                        tender_table = sel.xpath('../..')
                        sels = tender_table.xpath('.//tr')
                        break
                    
        if not sels:
            self.logger.debug(f'Cannot search the tender table: {response.url}')

        for k, sel in enumerate(sels):
            if k == 0:
                continue
            tds = sel.xpath(r'./td/text()')
            if not tds:
                self.logger.debug(f'The <tr> has no <td>: {sel}')
                self.logger.debug(f'The Error URL: {response.url}')
                continue
            item0 = TendercrabItem()
            item0['url'] = response.url
            item0['title'] = item['title'].strip('\xa0')
            item0['name'] = item['title'] + '-' + tds[1].extract()
            item0['name'] = item0['name'].strip('\xa0')
            item0['seller'] = tds[2].extract().strip('\xa0')
            item0['sellerAddress'] = tds[3].extract().strip('\xa0')
            item0['price'] = tds[4].extract().strip('\xa0')
            item0['publishDate'] = publishDate

            self.logger.debug(f"One item is yield: {item0}")
            yield item0

