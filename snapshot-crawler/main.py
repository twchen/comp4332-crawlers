#!/usr/bin/env python3

import subprocess
from datetime import datetime
import sys, os, re, pytz
import requests
import lxml.html
import argparse

terms = { '10': 'Fall', '20': 'Winter', '30': 'Spring', '40': 'Summer' }
snapshots_dir = 'all-snapshots'

def add_to_index(path):
    if os.path.exists(f'{snapshots_dir}/index.html'):
        index_file = f'{snapshots_dir}/index.html'
    else:
        index_file = 'snapshots_index.html'
    index = lxml.html.parse(index_file)
    ul = index.xpath('//ul')[0]
    snapshots_index = lxml.html.parse(os.path.join(path, 'index.html'))
    text = snapshots_index.xpath('//head/title/text()')[0].replace(': Snapshot taken', '')
    href = path[len(snapshots_dir)+1:]
    li = lxml.html.fromstring(f'<li><a href="{href}">{text}</a></li>')
    ul.append(li)
    index.write(f'{snapshots_dir}/index.html', encoding='UTF-8', method='html')

def push_to_git():
    subprocess.run('git add .', cwd=snapshots_dir, shell=True)
    subprocess.run('git commit -m "added new snapshot at $(TZ=Hongkong date +%m-%d\\ %H:%M)"',
                   stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, cwd=snapshots_dir, shell=True)
    subprocess.run('git push', stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, cwd=snapshots_dir, shell=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='https://w5.ab.ust.hk/wcq/cgi-bin/',
                        help='The start_url for crawler')
    parser.add_argument('-p', '--git-push', action='store_true',
                        help=f'Whether or not push all snapshots to a git repo. Note that the git repo should be set up at the directory {snapshots_dir}')
    args = parser.parse_args()
    start_url = args.url
    do_git_push = args.git_push

    r = requests.get(start_url)
    term_code = re.search(r'\d{4}', r.url).group()
    now = datetime.now(tz=pytz.timezone('Hongkong'))
    minute = '00' if now.minute < 30 else '30'
    path = '{}/20{}/{}/{}/{}'.format(snapshots_dir, term_code[:2], terms[term_code[2:]], now.strftime('%m/%d/%H'), minute)
    if os.path.exists(path):
        print('Pages already crawled')
        return
    res = subprocess.run('scrapy crawl snapshot -a start_url=%s' % start_url, shell=True)
    if res.returncode == 0:
        os.makedirs(path)
        subprocess.run(f'mv current-snapshot/* {path}', shell=True)
        add_to_index(path)
        if do_git_push:
            push_to_git()

if __name__ == '__main__':
    main()
