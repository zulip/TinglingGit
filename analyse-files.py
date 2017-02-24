import requests
from urlparse import urlparse
from collections import defaultdict
from tornado import httpclient, gen, ioloop, queues
from datetime import timedelta
import os
import sys
import json
import argparse
import subprocess

def build_changed_files_dir(diffs):
    files = defaultdict(list)
    for diff in diffs:
        for file in diffs[diff][0]:
            files[file['filename']].append((diff, file['additions'], file['deletions'], file['changes']))
    return files

@gen.coroutine
def fetch_diffs(all_open_pulls, concurrency=10):

    q = queues.Queue()
    fetching, fetched = set(), set()
    diffs = defaultdict(tuple)

    @gen.coroutine
    def fetch_diff():
        open_pull = yield q.get()
        try:
            if open_pull['url'] in fetching:
                return

            fetching.add(open_pull['url'])
            diff = yield httpclient.AsyncHTTPClient(defaults=dict(user_agent="MyUserAgent")).fetch(open_pull['url']+'/files?client_id=839a7c4a6d814e6287e9&client_secret=a91cf8513410fb64750374cf410607e4ab4a8bba', raise_error=False)
            if diff.code == 200:
                fetched.add(open_pull['url'])
                print("Fetched :%s" % open_pull['url'])
                diffs[open_pull['number']] = (json.loads(diff.body), open_pull['html_url'])
                if all_open_pulls:
                    q.put(all_open_pulls.pop())
            elif diff.code == 404:
                fetching.remove(open_pull['url'])
                print("Not Found:%s" % open_pull['url'])
            elif diff.code == 403:
                fetching.remove(open_pull['url'])
                print("Forbidden 403: " + open_pull['url'])
            else:
                q.put(open_pull)
                fetching.remove(open_pull['url'])

        finally:
            q.task_done()

    @gen.coroutine
    def worker():
        while True:
            yield fetch_diff()

    for _ in range(concurrency):
        if all_open_pulls:
            q.put(all_open_pulls.pop())

    for _ in range(concurrency):
        worker()

    yield q.join(timeout=timedelta(seconds=300))
    assert fetching == fetched
    raise gen.Return(diffs)

def fetch_open_pulls(upstream_path):

    all_pulls = []
    url = 'https://api.github.com/repos' + upstream_path + '/pulls?state=open&client_id=839a7c4a6d814e6287e9&client_secret=a91cf8513410fb64750374cf410607e4ab4a8bba'
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

@gen.coroutine
def sort_prs():
    print("Checking Directory for a Github repository...")
    upstream = check_for_gitrepo()
    print("Github upstream found\n===>%s" % upstream)

    upstream_path = urlparse(upstream).path.split('.git')[0]
    (owner, repo) = urlparse(upstream).path.split('.git')[0][1:].split('/')
    print("Fetching Open Pulls from Upstream")
    all_open_pulls = fetch_open_pulls(upstream_path)
    print("Fetching Open Pulls from Upstream Completed")
    print("Fetching Diffs for all Open Pulls")
    diffs = yield fetch_diffs(all_open_pulls)
    print("Fetching Diffs Completed\n")
    all_open_pulls = []
    for diff in diffs:
        changes = 0
        for file in diffs[diff][0]:
            changes += file['changes']
        all_open_pulls.append((diff, changes, diffs[diff][1]))
    all_open_pulls.sort(key=lambda x: x[1])

    for pull in all_open_pulls:
        print('\033[92m[%d]: %s\033[0m' % (pull[1], pull[2]))

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

def remove_prs(all_open_pulls, ignore_prs):

    for arg in ignore_prs:
        try:
            pr = int(arg)
            for x in range(0,len(all_open_pulls)):
                if all_open_pulls[x]['number'] == pr:
                    all_open_pulls = all_open_pulls[:x] + all_open_pulls[x+1:]
                    break
        except:
            print(arg + " Not a valid PR")
    return all_open_pulls

@gen.coroutine
def analyse(ignore_prs):

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
    all_open_pulls = remove_prs(all_open_pulls, ignore_prs)
    print("Fetching Open Pulls from Upstream Completed")

    print("Fetching Diffs for all Open Pulls")
    diffs = yield fetch_diffs(all_open_pulls)
    changed_files = build_changed_files_dir(diffs)
    print("Fetching Diffs Completed")

    unsafe_files = []
    for fn in curdir_files:
        if fn in changed_files:
            s = '\033[91m' + fn + '\033[0m'
            for pr in changed_files[fn]:
                s += ' [PR#'+str(pr[0])+'(+'+str(pr[1])+'-'+str(pr[2])+')'+']('+upstream.split('.git')[0]+'/pull/'+str(pr[0])+')'
            unsafe_files.append(s)
        else:
            print('\033[92m' + fn + '\033[0m')
    for fn in unsafe_files:
        print(fn)

def main():

    parser = argparse.ArgumentParser(description="Determine Possible conflicts with open PR's")
    parser.add_argument('--ignore-pr', metavar='N', type=int, nargs='+',
                        default=[],help="PR's to ignore for conflict determination")
    parser.add_argument('--sort-pr',default=False,action='store_true',
                        help="Sort the open PR's according to size of diffstats")
    args = parser.parse_args()
    io_loop = ioloop.IOLoop.current()
    if args.sort_pr:
        io_loop.run_sync(sort_prs)
    else:
        io_loop.run_sync(lambda : analyse(args.ignore_pr))

if __name__ == '__main__':
    main()
