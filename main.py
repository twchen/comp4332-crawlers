#!/usr/bin/env python3

import subprocess
from datetime import datetime
import sys, os, re, pytz
import requests
import lxml.html

terms = { '10': 'Fall', '20': 'Winter', '30': 'Spring', '40': 'Summer' }

def add_to_index(path):
    if os.path.exists('snapshots/index.html'):
        index_file = 'snapshots/index.html'
    else:
        index_file = 'snapshots_index.html'
    index = lxml.html.parse(index_file)
    ul = index.xpath('//ul')[0]
    snapshot_index = lxml.html.parse(os.path.join(path, 'index.html'))
    text = snapshot_index.xpath('//head/title/text()')[0].replace(': Snapshot taken', '')
    href = path[10:]
    li = lxml.html.fromstring('<li><a href="%s">%s</a></li>' % (href, text))
    ul.append(li)
    with open('snapshots/index.html', 'wb') as f:
        f.write(lxml.html.tostring(index))

def push_to_git():
    subprocess.run('git add .', cwd='snapshots', shell=True)
    subprocess.run('git commit -m "added new snapshot at $(TZ=Hongkong date +%m-%d\ %H:%M)" >/dev/null 2>&1', cwd='snapshots', shell=True)
    subprocess.run('git push', cwd='snapshots', shell=True)

def main():
    if len(sys.argv) == 1:
        start_url = 'https://w5.ab.ust.hk/wcq/cgi-bin/'
    elif len(sys.argv) == 2:
        start_url = sys.argv[1]
    else:
        print('Usage: %s [start_url]' % sys.argv[0])
        sys.exit(1)
    r = requests.get(start_url)
    term_code = re.search(r'\d{4}', r.url).group()
    now = datetime.now(tz=pytz.timezone('Hongkong'))
    minute = '00' if now.minute < 30 else '30'
    path = 'snapshots/20{}/{}/{}/{}'.format(term_code[:2], terms[term_code[2:]], now.strftime('%m/%d/%H'), minute)
    if os.path.exists(path):
        print('Pages already crawled')
        return
    res = subprocess.run('scrapy crawl snapshot -a start_url=%s' % start_url, shell=True, cwd='spider')
    if res.returncode == 0:
        os.makedirs(path)
        subprocess.run('mv spider/snapshot/* %s' % path, shell=True)
        add_to_index(path)
        #push_to_git()

if __name__ == '__main__':
    main()
