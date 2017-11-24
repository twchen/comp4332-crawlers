#!/usr/bin/env python3

import subprocess
from datetime import datetime
import sys, os, re, pytz
import requests

terms = { '10': 'Fall', '20': 'Winter', '30': 'Spring', '40': 'Summer' }


def get_term_dir(term_code):
    term_code = re.search(r'\d{4}', url).group()
    return '20%s/%s' % (term_code[:2], terms[term_code[-2:]])

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
    path = 'snapshots/20%s/%s/%s' % (term_code[:2], terms[term_code[2:]], now.strftime('%m/%d/%H'))
    if os.path.exists(path):
        print('Pages already crawled')
        return
    res = subprocess.run('scrapy crawl courses -a start_url=%s' % start_url, shell=True, cwd='spider')
    if res.returncode == 0:
        os.makedirs(path)
        subprocess.run('mv spider/snapshot/* %s' % path, shell=True)

if __name__ == '__main__':
    main()