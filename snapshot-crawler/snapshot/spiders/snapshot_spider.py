import scrapy
from datetime import datetime
import lxml.html
import os
import pytz
from datetime import datetime
import copy
from scrapy.utils.conf import closest_scrapy_cfg

class SnapshotSpider(scrapy.Spider):
    name = 'snapshot'

    def __init__(self, *args, **kwargs):
        super(SnapshotSpider, self).__init__(*args, **kwargs)
        if 'start_url' in kwargs:
            self.start_urls = [kwargs.get('start_url')]
        elif 'start_urls' in kwargs:
            self.start_urls = kwargs.get('start_urls').split(',')
        else:
            self.start_urls = [ 'https://w5.ab.ust.hk/wcq/cgi-bin/' ]
        now = datetime.now(tz=pytz.timezone('Hongkong'))
        minute = '00' if now.minute < 30 else '30'
        self.time = now.strftime('%Y-%m-%d %H:') + minute
        self.template = lxml.html.parse('template.html')
        proj_root = os.path.dirname(closest_scrapy_cfg())
        # store the current snapshot at the directory self.snapshot_dir
        self.snapshot_dir = os.path.join(proj_root, 'current-snapshot')
        os.makedirs(f'{self.snapshot_dir}/subjects', exist_ok=True)

    def parse(self, response):
        index = copy.deepcopy(self.template)
        depts = index.xpath('//div[@class="depts"]')[0]
        self.term = response.xpath('//li[@class="term"]//a[@onclick]/text()').extract_first().strip()
        title = index.xpath('//head/title')[0]
        title.text = f'{self.term}: Snapshot taken at {self.time}'
        for a in response.xpath('//div[@class="depts"]/a'):
            el = lxml.html.fromstring(a.extract())
            dept = el.get('href').split('/')[-1]
            el.set('href', f'subjects/{dept}.html')
            depts.append(el)
            yield response.follow(a, callback=self.parse_dept)
        index.write(f'{self.snapshot_dir}/index.html', encoding='UTF-8', method='html')

    def parse_dept(self, response):
        index = copy.deepcopy(self.template)
        depts = index.xpath('//div[@class="depts"]')[0]
        # change absolute links to relative links
        for a in response.xpath('//div[@class="depts"]/a'):
            el = lxml.html.fromstring(a.extract())
            dept = el.get('href').split('/')[-1]
            el.set('href', f'{dept}.html')
            depts.append(el)
        classes = lxml.html.fromstring(response.xpath('//div[@id="classes"]')[0].extract())
        index.xpath('//body')[0].append(classes)
        # remove the links for instructors
        for link in index.xpath('//td/a[contains(@href, "instructor")]'):
            link.tail = link.text
            link.drop_tree()
        dept = response.url.split('/')[-1]
        title = index.xpath('//head/title')[0]
        title.text = f'{self.term} {dept}: Snapshot taken at {self.time}'
        index.write(f'{self.snapshot_dir}/subjects/{dept}.html', encoding='UTF-8', method='html')

    def closed(self, reason):
        print('Crawling completed')
