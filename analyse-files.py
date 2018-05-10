import requests
from urlparse import urlparse
from collections import defaultdict
from tornado import httpclient, gen, ioloop, queues
from datetime import timedelta, datetime
from collections import deque
import os
import sys
import json
import argparse
import subprocess
import configparser

TINGLINGGIT_ROOT = os.path.split(os.path.abspath(__file__))[0]
TINGLINGGIT_SETTINGS_PATH = os.path.join(TINGLINGGIT_ROOT, 'tinglinggit.ini')

config = configparser.ConfigParser()
config.read(TINGLINGGIT_SETTINGS_PATH)

access_token = config['GITHUB']['GITHUB_TOKEN']

if access_token == 'add-token-here':
    print('Please configure Github Authentication settings in tinglinggit.ini.')
    exit(1)

# This function could be used to specify the script for repetitive task.
@gen.coroutine
def execute_task(fn, associated_prs=[], root_dir='', rebase_check=False):
    # Remove this return statement after adding custom SCRIPT
    return -1

    COMMON_PREFIX_COMMIT_MSG = ''
    # NOTE: Do not modify values of fn, associated_prs or root_dir in the custom script.
    # #######SCRIPT BEGINS HERE#########
    ####################################
    # #######SCRIPT ENDS HERE###########

    # raw_input() to wait for review upon changes and  proceed further
    raw_input()

    # Commit changes done to file
    commit_cur_change = subprocess.check_output(
                        ['git', 'add', os.path.join(root_dir,fn)]).strip()
    commit_cur_change = subprocess.check_output(
                        ['git', 'commit', '-m', COMMON_PREFIX_COMMIT_MSG+" "+fn.split('/')[-1]+"."]).strip()
    commit_status = 1
    print(commit_cur_change)
    current_branch = subprocess.check_output(
                     ['git', 'status']).strip().split('\n')[0].split(' ')[-1]
    print(current_branch)

    if not rebase_check:
        associated_prs = []

    for prnum in associated_prs:
        t = subprocess.check_output(('git fetch upstream pull/%s/head:test-%s' % (prnum,prnum)).split(' ')).strip()
        t = subprocess.check_output(('git checkout test-%s' % (prnum)).split(' ')).strip()

        try:
            check_cur_commit = subprocess.check_output(
                               ('git rebase %s' % (current_branch)).split(' ')).strip()
        except:
            t = subprocess.check_output('git rebase --abort'.split(' ')).strip()
            commit_status = 0

        t = subprocess.check_output(('git checkout %s' % (current_branch)).split(' ')).strip()
        t = subprocess.check_output(('git branch -D test-%s' % (prnum)).split(' ')).strip()
        print(t)
        if not commit_status:
            break
    # If commit is not safe, revert the last commit
    if not commit_status:
        t = subprocess.check_output('git reset --hard HEAD~1'.split(' ')).strip()
        print(t)
        return 0
    else:
        return 1

def build_changed_files_dir(diffs):
    files = defaultdict(list)
    for diff in diffs:
        for file in diffs[diff][0]:
            files[file['filename']].append((diff, file['additions'], file['deletions'], file['changes']))
    return files

@gen.coroutine
def fetch_all_open_issues(upstream_path, concurrency=10):

    q = queues.Queue()
    fetching, fetched = set(), set()
    open_issues = deque()

    url = 'https://api.github.com/repos' + upstream_path + '/issues?state=open&access_token=' + access_token
    responce = requests.get(url)
    links = responce.headers['Link'].split(', ')
    print("Fetched: %s" % url)
    for link in links:
        if 'last' in link.split('; ')[1]:
            url = link.split('; ')[0][1:][:-1]
            break
    queries = urlparse(url).query.split('&')
    last_page = 1
    for query in queries:
        if 'page=' in query:
            last_page = int(query.split('=')[1])
            break
    url_fetch_list = []
    for i in range(1, last_page + 1):
        url_fetch_list.append('https://api.github.com/repos' + upstream_path + '/issues?state=open&access_token=' + access_token + '&page=' + str(i))

    @gen.coroutine
    def fetch_diff():
        url = yield q.get()
        try:
            if url in fetching:
                return

            fetching.add(url)
            issues = yield httpclient.AsyncHTTPClient(defaults=dict(user_agent="MyUserAgent")).fetch(url, raise_error=False)
            if issues.code == 200:
                fetched.add(url)
                print("Fetched :%s" % url)
                open_issues.extend(json.loads(issues.body))
                if url_fetch_list:
                    q.put(url_fetch_list.pop())
            elif issues.code == 404:
                fetching.remove(url)
                print("Not Found:%s" % open_pull['url'])
            elif issues.code == 403:
                fetching.remove(url)
                print("Forbidden 403: " + url)
            else:
                q.put(url)
                fetching.remove(url)

        finally:
            q.task_done()

    @gen.coroutine
    def worker():
        while True:
            yield fetch_diff()

    for _ in range(concurrency):
        if url_fetch_list:
            q.put(url_fetch_list.pop())

    for _ in range(concurrency):
        worker()

    yield q.join(timeout=timedelta(seconds=300))
    assert fetching == fetched
    raise gen.Return(open_issues)

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
            diff = yield httpclient.AsyncHTTPClient(defaults=dict(user_agent="MyUserAgent")).fetch(open_pull['url']+'/files?access_token=' + access_token, raise_error=False)
            if diff.code == 200:
                fetched.add(open_pull['url'])
                print("Fetched :%s" % open_pull['url'])
                diffs[open_pull['number']] = (json.loads(diff.body), open_pull['html_url'], open_pull['title'])
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
    url = 'https://api.github.com/repos' + upstream_path + '/pulls?state=open&access_token=' + access_token
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

    git_tracking_rootdir = subprocess.check_output(
                           'git rev-parse --show-toplevel'.split(' ')).strip()

    files = filter(os.path.isfile,os.listdir(os.getcwd()))
    files = [ os.path.relpath(os.path.join(os.getcwd(),file),
              git_tracking_rootdir) for file in files]

    return sorted(files, key= lambda file_path: file_path.split('/')[-1])

def get_files_in_curdir_recursive():

    git_tracking_rootdir = subprocess.check_output(
                           'git rev-parse --show-toplevel'.split(' ')).strip()

    files = []
    for (dirroot, subdirs, dirfiles) in os.walk(os.getcwd()):
        files = files + [ os.path.relpath(os.path.join(dirroot, file),
                  git_tracking_rootdir) for file in dirfiles]

    return files

@gen.coroutine
def sort_prs():
    print("Checking Directory for a Github repository...")
    upstream = check_for_gitrepo()
    print("Github upstream found\n===>%s" % upstream)

    upstream_path = urlparse(upstream).path.split('.git')[0]
    if '@' in upstream_path:
        upstream_path = '/' + upstream_path.split(':')[1]
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
        all_open_pulls.append((diff, changes, diffs[diff][1], diffs[diff][2]))
    all_open_pulls.sort(key=lambda x: x[1])

    for pull in all_open_pulls:
        print('\033[92m[%d]: %s (%s)\033[0m' % (pull[1], pull[3], pull[2]))

def all_in(list1, list2):
    for item in list1:
        if item not in list2:
            return False
    return True

@gen.coroutine
def stale_issues(labels, older_then, break_on):
    print("Checking Directory for a Github repository...")
    upstream = check_for_gitrepo()
    print("Github upstream found\n===>%s" % upstream)

    upstream_path = urlparse(upstream).path.split('.git')[0]
    if '@' in upstream_path:
        upstream_path = '/' + upstream_path.split(':')[1]
    (owner, repo) = urlparse(upstream).path.split('.git')[0][1:].split('/')
    print("Fetching Open issues from Upstream")
    open_issues = yield fetch_all_open_issues(upstream_path)
    print("Fetching Open issues from Upstream Completed")
    list_stale_issues = []
    for issue in open_issues:
        if datetime.strptime(issue['updated_at'], '%Y-%m-%dT%H:%M:%SZ') < older_then:
            list_stale_issues.append(issue)
    label_filter_stale_issues = []
    for issue in list_stale_issues:
        issue_labels = [label['name'] for label in issue['labels']]
        if all_in(labels, issue_labels):
            label_filter_stale_issues.append(issue)
    print("Fetched %d Issues" % len(label_filter_stale_issues))
    if break_on:
        break_issues_on_label = defaultdict(list)
        for issue in label_filter_stale_issues:
            for label in issue['labels']:
                if break_on[0] in label['name']:
                    break_issues_on_label[label['name']].append(issue)
        break_issues_on_label = sorted(break_issues_on_label.items(), key= lambda (k,v): len(v))
        for label in break_issues_on_label:
            issues = label[1]
            print("\nLabel '%s' has %d issues." % (label[0], len(issues)))
            for issue in issues:
                print('\033[92m %s\033[0m' % issue['html_url'])
    else:
        for issue in label_filter_stale_issues:
            print('\033[92m %s\033[0m' % issue['html_url'])

def check_for_gitrepo():

    git_status = subprocess.check_output('git status'.split(' '))

    if 'Not a git repository' in git_status:
        print('Not a git repository')
        sys.exit(1)

    upstream = subprocess.check_output('git config --get remote.upstream.url'.split(' '))

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
def do_repetitive_task_safely(curdir_files, changed_files, rebase_check):
    potential_unsafe_files = [fn for fn in curdir_files if fn in changed_files]
    safe_files = [fn for fn in curdir_files if fn not in changed_files]
    safely_done = []
    git_tracking_rootdir = subprocess.check_output(
                           'git rev-parse --show-toplevel'.split(' ')).strip()
    print("Beginning to perform repetitive task over files.")
    for fn in safe_files:
        status = yield execute_task(fn, root_dir=git_tracking_rootdir, rebase_check=rebase_check)
        if status == 1:
            safely_done.append(fn)
        elif status == -1:
            print("ERROR: Custom script not added.")
    for fn in potential_unsafe_files:
        associated_prs = [str(pr[0]) for pr in changed_files[fn]]
        status = yield execute_task(fn, associated_prs, root_dir=git_tracking_rootdir, rebase_check=rebase_check)
        if status == 1:
            safely_done.append(fn)
        elif status == -1:
            print("ERROR: Custom script not added.")
    # Print Filenames which were safely commited
    for fn in safely_done:
        print("'%s'," % (fn))


@gen.coroutine
def analyse(ignore_prs, recursive, selective, safe_rep, rebase_check):

    print("Checking Directory for a Github repository...")
    upstream = check_for_gitrepo()
    print("Github upstream found\n===>%s" % upstream)

    upstream_path = urlparse(upstream).path.split('.git')[0]

    if '@' in upstream_path:
        upstream_path = '/' + upstream_path.split(':')[1]
    (owner, repo) = urlparse(upstream).path.split('.git')[0][1:].split('/')
    if selective:
        print("Selective files mode. Enter newline char seperated filenames to be checked.\n'$'should be entered to mark End of Input.")
        curdir_files = []
        temp = raw_input()
        while not temp == '$':
            curdir_files.append(temp)
            temp = raw_input()
    elif recursive:
        curdir_files = get_files_in_curdir_recursive()
    else:
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
                s += ' [PR#'+str(pr[0])+'(+'+str(pr[1])+'-'+str(pr[2])+')'+'](https://github.com'+upstream_path+'/pull/'+str(pr[0])+')'
            unsafe_files.append(s)
        else:
            print('\033[92m' + fn + '\033[0m')
    for fn in unsafe_files:
        print(fn)

    if safe_rep:
        yield do_repetitive_task_safely(curdir_files, changed_files, rebase_check)

def main():

    parser = argparse.ArgumentParser(description="Determine Possible conflicts with open PR's")
    parser.add_argument('--ignore-pr', metavar='N', type=int, nargs='+',
                        default=[],help="PR's to ignore for conflict determination")
    parser.add_argument('--sort-pr',default=False,action='store_true',
                        help="Sort the open PR's according to size of diffstats")
    parser.add_argument('--stale-issues',default=False,action='store_true',
                        help="This shows all issues in repo which have become stale (By Default older than 30 days)")
    parser.add_argument('--older-then',metavar='N', type=str, nargs=1,default=False,
                        help="This shows all issues in repo which have become stale and older then given date(Format for date is strictly YYYYMMDD)")
    parser.add_argument('--labels', metavar='N', type=str, nargs='+',
                        default=[],help="Labels to filter issues on. Use labels exactly they were defined for a Repo.\nExample 'area: tooling'")
    parser.add_argument('--break-on', metavar='N', type=str, nargs=1,
                        default=False,help="Using this we can break the list of issues based on a string in labels list.")
    parser.add_argument('--recursive', default=False, action='store_true',
                        help="Using this we can walk the current Directory recursively for checking files.")
    parser.add_argument('--selective', default=False, action='store_true',
                        help="Using this we can provide a selective list of files as input which will be classified as safe and unsafe.\nGenerally this option is used with a file redirected to input stream containing file names seperated by newline char.\nNote:End of input is marked by inputing a '$' symbol.")
    parser.add_argument('--safe-rep', default=False, action='store_true',
                        help="Using this we can perform repetitive tasks upon different files and commit only changes which are\nsafe with respect to causing merge conflicts to other PR's.\nThe code to handle repetitive task could be placed\nby developer under execute_task() function.")
    parser.add_argument('--rebase-check', default=False, action='store_true',
                        help="Using this while performing repetitive tasks, we can do a rebase over PR's which might get\nconflicted by changes to a particular file and see if that actually\nhappens and commit or revert the commit accordingly.")
    args = parser.parse_args()
    io_loop = ioloop.IOLoop.current()
    if args.sort_pr:
        io_loop.run_sync(sort_prs)
    elif args.stale_issues:
        if args.older_then:
            older_then = datetime.strptime(args.older_then[0], '%Y%m%d')
        else:
            older_then = (datetime.now() - timedelta(days=30))
        io_loop.run_sync(lambda : stale_issues(args.labels, older_then, args.break_on))
    elif not args.older_then and not args.labels and not args.break_on:
        io_loop.run_sync(lambda : analyse(args.ignore_pr, args.recursive, args.selective, args.safe_rep, args.rebase_check))
    else:
        print("Params not in correct combination")

if __name__ == '__main__':
    main()
