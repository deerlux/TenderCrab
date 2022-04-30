import scrapy
import re
import csv
from scrapy.http import HtmlResponse as Response
from TenderCrab.DataModels import Session, TenderItem
import sqlalchemy as sa


class GettitleSpider(scrapy.Spider):
    name = 'GetTitle'
    allowed_domains = ['ccgp-shandong.gov.cn']
    start_urls = ['http://ccgp-shandong.gov.cn/sdgp2017/site/listnew.jsp?grade=province&colcode=0302']
    url_set = set()
    session = Session()

    def __init__(self, pages=None, *args, **kwargs):
        super(GettitleSpider, self).__init__(*args, **kwargs)
        if pages:
            self.pages = int(pages)
        else:
            self.pages = None
        
        self.session = Session()

        # 以下对数据库的内容进行更新
        if self.url_set:
            return

        with open('nulltitle.csv') as f:
            reader = csv.reader(f)
            for row in reader:
                self.url_set.add(row[1])

    def parse(self, response: Response):
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
            if crawl_pages == 1:
                yield

            for i in range(curpage + 1, crawl_pages + 1):
                url = f'{base_url}?curpage={i}&colcode={colcode}&grade={grade}'
                # self.logger.info(f'Starting... colcode: {colcode}, curpage: {i}')
                self.logger.info(f'Yield URL: {url}')
                yield response.follow(url, self.parse)
        
        # 找未抓取标题的页面
        links = response.css('span.title span a')
        for link in links:
            url = link.attrib["href"]
            url = response.urljoin(url)
            # 如果这里面
            if url in self.url_set:
                title = link.attrib["title"]
                stmt = sa.select(TenderItem).where(TenderItem.url == url)
                item = self.session.scalars(stmt).one()
                item.title = title
                self.session.commit()
                self.logger.info(f'The url\'s title is updated: {url}')

        pass
