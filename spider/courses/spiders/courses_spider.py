import scrapy
from datetime import datetime
import lxml.html
import os, re

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
        os.makedirs('snapshot/subjects', exist_ok=True)

    def parse(self, response):
        index = lxml.html.parse('index_template.html')
        depts = index.xpath('//div[@class="depts"]')[0]
        for a in response.css('div.depts a'):
            el = lxml.html.fromstring(a.extract())
            el.set('href', 'subjects/%s.html' % el.get('href').split('/')[-1])
            depts.append(el)
            yield response.follow(a, callback=self.parse_dept)
        with open('snapshot/index.html', 'wb') as f:
            f.write(lxml.html.tostring(index))

    def parse_dept(self, response):
        root = lxml.html.fromstring(response.body)
        # remove irrelevant menu bars
        for rule in ['div#HKUSTBar', 'ul[class="topbar clearfix"]']:
            el = root.cssselect(rule)[0]
            el.getparent().remove(el)
        # change absolute links to relative links
        for link in root.cssselect('div.depts > a'):
            href = link.get('href')
            link.set('href', href.split('/')[-1] + '.html')
        # remove the links for instructors
        for link in root.cssselect('td > a[href*="instructor"]'):
            link.tail = link.text
            link.drop_tree()
        filepath = 'snapshot/subjects/%s.html' % response.url.split('/')[-1]
        with open(filepath, 'wb') as f:
            s = lxml.html.tostring(root)
            # link js and css files to the original website
            f.write(s.replace(b'/wcq/', b'https://w5.ab.ust.hk/wcq/'))
