# TinglingGit
This is a tool which helps to avoid introducing merge conflicts for open PR's in a Github repo by creating new PR's which may get merged sooner resulting in merge conflicts for other folks working on other PR's and rebasing to upstream. Also this tool can list all open PR's in increasing order of changes made. This feature may be useful for maintainers while clearing backlog on PR's.

# How Things Work here
So When this tool is run from a terminal with prompt sitting in a Git tracked directory, this tool starts to look for Github remote upstream and fetches stuff from Github and report whether the files in current directory are being modified in any of the open PR's. Files safe to modify are green but red otherwise.

# To Run the tool

* Clone or download and extract this repository.
* Open the TinglingGit Directory in terminal and install dependancies.<br>
  ` pip install -r requirements.txt `
* Open a terminal to a git tracked directory with upstream setup for remote repo.
* Run the tool from within the Directory you wanna analyse files for.<br>
  ` python /path/to/TinglingGit/analyse-files.py `
* One may optionally specify a list of PR numbers to exclude from consideration.<br>
  ` python /path/to/TinglingGit/analyse-files.py --ignore-pr 3658 4125` will exclude PR 3658 and 4125 from consideration.
* After tool successfully completes executing files are displayed with green to represent safe and red to represent possible merge conflicts.
* If we want to list the PR's in increasing order of changes introduced by the PR. Simple do<br>
  ` python /path/to/TinglingGit/analyse-files.py --sort-pr`
* An output of following patter will come at end<br>
    [1]: https://github.com/zulip/zulip/pull/3690<br>
    [2]: https://github.com/zulip/zulip/pull/2254<br>
    [3]: https://github.com/zulip/zulip/pull/3749<br>
    [3]: https://github.com/zulip/zulip/pull/1935<br>

  Here `[number]` means the number of changes introduced in that PR.

#TODO

* Improve Readme.
