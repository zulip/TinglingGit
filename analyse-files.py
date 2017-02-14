import requests
from urlparse import urlparse
from collections import defaultdict
from tornado import httpclient, gen, ioloop, queues
from datetime import timedelta
import os
import sys
import subprocess

@gen.coroutine
def build_changed_files_dir(all_open_pulls, concurrency=20):

    q = queues.Queue()
    fetching, fetched = set(), set()
    diffs = defaultdict(str)

    @gen.coroutine
    def fetch_diffs():
        open_pull = yield q.get()
        try:
            if open_pull['diff_url'] in fetching:
                return

            fetching.add(open_pull['diff_url'])
            diff = yield httpclient.AsyncHTTPClient().fetch(open_pull['diff_url'], raise_error=False)
            if diff.code == 200:
                fetched.add(open_pull['diff_url'])
                print("Fetched Diff:%s" % open_pull['diff_url'])
                diffs[open_pull['number']] = diff.body
                if all_open_pulls:
                    q.put(all_open_pulls.pop())
            else:
                #all_open_pulls.append(open_pull)
                fetching.remove(open_pull['diff_url'])

        finally:
            q.task_done()

    @gen.coroutine
    def worker():
        while True:
            yield fetch_diffs()

    for _ in range(concurrency):
        if all_open_pulls:
            q.put(all_open_pulls.pop())

    for _ in range(concurrency):
        worker()

    yield q.join(timeout=timedelta(seconds=300))
    assert fetching == fetched
    files = defaultdict(list)
    for diff in diffs:
        lines = diffs[diff].split('\n')
        lines = [line for line in lines if line.startswith('diff')]
        for line in lines:
            files[line.split(' ')[2][2:]].append(diff)

    raise gen.Return(files)

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

def remove_prs(all_open_pulls):

    for arg in sys.argv[1:]:
        try:
            pr = int(arg)
            for x in range(0,len(all_open_pulls)):
                if all_open_pulls[x]['number'] == pr:
                    all_open_pulls = all_open_pulls[:x] + all_open_pulls[x+1:]
                    break
        except:
            print(arg+" Not a valid PR")
    return all_open_pulls

@gen.coroutine
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
    all_open_pulls = remove_prs(all_open_pulls)
    print("Fetching Open Pulls from Upstream Completed")

    print("Fetching Diffs for all Open Pulls")
    changed_files = yield build_changed_files_dir(all_open_pulls)
    print("Fetching Diffs Completed")

    for fn in curdir_files:
        if fn in changed_files:
            print('\033[91m' + fn + '\033[0m')
        else:
            print('\033[92m' + fn + '\033[0m')

if __name__ == '__main__':
    io_loop = ioloop.IOLoop.current()
    io_loop.run_sync(analyse)
