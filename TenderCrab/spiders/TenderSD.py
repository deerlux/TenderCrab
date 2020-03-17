# -*- coding: utf-8 -*-
import scrapy
from TenderCrab.items import TendercrabItem
from dateutil.parser import parse, ParserError


class TendersdSpider(scrapy.Spider):
    name = 'TenderSD'
    # /sdgp2017/site/channelall.jsp'
    allowed_domains = ['www.ccgp-shandong.gov.cn']
    start_urls = ['http://www.ccgp-shandong.gov.cn/sdgp2017/site/channelall.jsp?colcode=0302',
        'http://www.ccgp-shandong.gov.cn/sdgp2017/site/channelall.jsp?colcode=0304']

    # rules = (
    #     Rule(LinkExtractor(allow=r'&id=\d+'), callback='parse_item', follow=True),
    # )

    def parse(self, response):
        # ---- 首先将有链接的标讯提取出来，然后送给另外一个回调函数去解析
        sels = response.xpath(r'//td[@class="Font9"]')
        # 只在前面的td中找相关的链接
        sels.pop(-1)
        self.logger.debug(f'Find {len(sels)} urls.....')
        for sel in sels:
            temp = sel.xpath(r'./text()').extract()
            if not temp:
                self.logger.debug(f'There is not data to extract: {sel}')
                continue
            publishDate = None
            cb_kwargs = {'publishDate': None}
            # 获取发布时间
            for strDate in temp:
                try:
                    publishDate = parse(strDate)
                except ParserError:
                    continue
            if publishDate:
                cb_kwargs['publishDate'] = publishDate
            
            relativeUrl = sel.xpath(r'./a/@href').extract()[0]            
            rootUrl = '/'.join(response.url.split('/')[0:3])
            requestUrl = rootUrl + relativeUrl

            self.logger.debug(f'Yield URL: {requestUrl}')
            request = scrapy.Request(
                requestUrl,
                callback=self.parse_item,
                cb_kwargs=cb_kwargs
                )
            yield request

        # # ---- 然后将所有的页进行解析返回
        # sels = response.xpath(r'//td[@class="Font9"]/a')
        # # 最后一个指出尾页的数字 javascript:query(1756)
        # endPageScr = sels[-1].xpath(r'./@href').extract()[0]
        # endPage = int(re.findall(r'\d+', endPageScr)[0])
        # # 遍历每一页
        # for k, page in enumerate(range(endPage)):
        #     if k == 0:
        #         continue
        #     else:
        #         request = scrapy.Request(f'{response.url}&curpage={k + 1}', callback=self.parse)
        #         yield request

    def parse_item(self, response, publishDate):
        # self.logger.debug(f'Parsing URL: {response.url}')
        item = TendercrabItem()
        item['url'] = response.url
        try:
            item['title'] = response.xpath(r'//div[@align="center"]//text()').extract()[0].strip('\xa0')
        except IndexError as e:
            self.logger.error(e)
            self.logger.debug(f'The Error URL: {response.url}')
            yield None

        sels = response.xpath(r'//table[@id="NoticeDetail"]//tr')
        # 如果没有搜到，可能这个URL地址没有中标清单表
        if not sels:
            self.logger.debug(f'This url has no "NoticeDetail" table: {response.url}')
            yield None

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

            # self.logger.debug(f"One item is yield: {item0}")
            yield item0
