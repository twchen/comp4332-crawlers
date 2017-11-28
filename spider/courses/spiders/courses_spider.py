import scrapy
from datetime import datetime
import lxml.html
import os, re
import pytz
from datetime import datetime
import copy

class CoursesSpider(scrapy.Spider):
    name = 'courses'

    def __init__(self, *args, **kwargs):
        super(CoursesSpider, self).__init__(*args, **kwargs)
        if 'start_url' in kwargs:
            self.start_urls = [kwargs.get('start_url')]
        elif 'start_urls' in kwargs:
            self.start_urls = kwargs.get('start_urls').split(',')
        else:
            self.start_urls = ['https://w5.ab.ust.hk/wcq/cgi-bin/']
        self.time = datetime.now(tz=pytz.timezone('Hongkong')).strftime('%Y-%m-%d %H:%M')
        self.template = lxml.html.parse('template.html')
        os.makedirs('snapshot/subjects', exist_ok=True)

    def parse(self, response):
        index = copy.deepcopy(self.template)
        depts = index.xpath('//div[@class="depts"]')[0]
        self.term = response.xpath('//li[@class="term"]//a[@onclick]/text()').extract_first().strip()
        title = index.xpath('//head/title')[0]
        title.text = '%s: Snapshot taken at %s' % (self.term, self.time)
        for a in response.xpath('//div[@class="depts"]/a'):
            el = lxml.html.fromstring(a.extract())
            el.set('href', 'subjects/%s.html' % el.get('href').split('/')[-1])
            depts.append(el)
            yield response.follow(a, callback=self.parse_dept)
        with open('snapshot/index.html', 'wb') as f:
            f.write(lxml.html.tostring(index))

    def parse_dept(self, response):
        index = copy.deepcopy(self.template)
        depts = index.xpath('//div[@class="depts"]')[0]
        # change absolute links to relative links
        for a in response.xpath('//div[@class="depts"]/a'):
            el = lxml.html.fromstring(a.extract())
            el.set('href', '%s.html' % el.get('href').split('/')[-1])
            depts.append(el)
        classes = lxml.html.fromstring(response.xpath('//div[@id="classes"]')[0].extract())
        index.xpath('//body')[0].append(classes)
        # remove the links for instructors
        for link in index.xpath('//td/a[contains(@href, "instructor")]'):
            link.tail = link.text
            link.drop_tree()
        dept = response.url.split('/')[-1]
        title = index.xpath('//head/title')[0]
        title.text = '%s %s: Snapshot taken at %s' % (self.term, dept, self.time)
        with open('snapshot/subjects/%s.html' % dept, 'wb') as f:
            f.write(lxml.html.tostring(index))
