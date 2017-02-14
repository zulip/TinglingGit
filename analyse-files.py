import requests
from urlparse import urlparse
from collections import defaultdict
import os
import sys
import subprocess

def build_changed_files_dir(all_open_pulls):

    files = defaultdict(list)
    for open_pull in all_open_pulls:
        diff_url = open_pull['diff_url']
        diff = requests.get(diff_url)
        lines = diff.text.split('\n')
        lines = [line for line in lines if line.startswith('diff')]
        for line in lines:
            files[line.split(' ')[2][2:]].append(open_pull['number'])
        print("Fetched Diff:%s" % diff_url)

    return files

def fetch_open_pulls(upstream_path):

    all_pulls = []
    url = 'https://api.github.com/repos' + upstream_path + '/pulls?state=open'
    while url:
        responce = requests.get(url)
        all_pulls += responce.json()
        links = responce.headers['Link'].split(', ')
        print("Fetched: %s" % url)
        url = ''
        for link in links:
            if 'next' in link.split('; ')[1]:
                url = link.split('; ')[0][1:][:-1]
                break

    return all_pulls

def get_files_in_curdir():

    git_tracking_rootdir = subprocess.Popen(
                           'git rev-parse --show-toplevel'.split(' '),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT).stdout.read().strip()

    files = filter(os.path.isfile,os.listdir(os.getcwd()))
    files = [ os.path.relpath(os.path.join(os.getcwd(),file),
              git_tracking_rootdir) for file in files]

    return files

def check_for_gitrepo():

    git_status = subprocess.Popen('git status'.split(' '),
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)

    if 'Not a git repository' in git_status.stdout.read():
        print('Not a git repository')
        sys.exit(1)

    upstream = subprocess.Popen('git config --get remote.upstream.url'.split(' '),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
    upstream = upstream.stdout.read()

    if upstream and 'github.com' in upstream:
        return upstream

    print('No Github "upstream" found in Current Directory')
    sys.exit(1)

def analyse():

    print("Checking Directory for a Github repository...")
    upstream = check_for_gitrepo()
    print("Github upstream found\n===>%s" % upstream)
    upstream_path = urlparse(upstream).path.split('.git')[0]
    (owner, repo) = urlparse(upstream).path.split('.git')[0][1:].split('/')
    curdir_files = get_files_in_curdir()
    if len(curdir_files) < 1:
        print('No Files to check Possible conflicts in Current Directory')
        sys.exit(1)
    print("Fetching Open Pulls from Upstream")
    all_open_pulls = fetch_open_pulls(upstream_path)
    print("Fetching Open Pulls from Upstream Completed")
    print("Fetching Diffs for all Open Pulls")
    changed_files = build_changed_files_dir(all_open_pulls)
    print("Fetching Diffs Completed")
    for fn in curdir_files:
        if fn in changed_files:
            print('\033[91m' + fn + '\033[0m')
        else:
            print('\033[92m' + fn + '\033[0m')

if __name__ == '__main__':
    analyse()
