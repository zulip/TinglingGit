# TinglingGit

TinglingGit is a tool for doing large migrations in a codebase without
creating merge conflicts.  Large code migrations (e.g. to adjust code
formatting, rename something that appears a lot, etc.) can often be
done with automated tools.  However, it's often painful to do so,
because they can create huge numbers of merge conflicts with
in-progress work on the project.

TinglingGit solves this problem by allowing a developer to scan all
the open pull requests in a codebase to see which files one can
migrate without any merge conflict risk (because 0 open PRs touch the
file), which ones can be migrated with minimal risk (because the PRs
touching them only make tiny changes), and for those files which are
likely to create a lot of merge conflicts, which PRs you should try to
merge before migrating them.

With this technique, one can do major migrations on a large codebase
with minimal disruption to the rest of the development community.  The
Zulip project has found this tool invaluable for the following
migrations of our codebase, in each case with 100-200 open PRs at the
time:

* Updating all of our HTML templates to use consistent 4-space
  indentation.
* Migrating our Python codebase from using the Python 2 syntax for
  mypy type annotations to the PEP-484 Python 3 syntax (which requires
  changing the `def` line of every function).

As a side effect of how it works, you can also use it to just get a
list of open PRs sorted by size of diffstat, which can be useful if
one is trying to prioritize integrating larger PRs.

# How Things Work here

So When this tool is run from a terminal with prompt sitting in a Git
tracked directory, this tool starts to look for Github remote upstream
and fetches stuff from Github and report whether the files in current
directory are being modified in any of the open PR's. Files safe to
modify are green but red otherwise.

# To Run the tool

* Clone or download and extract this repository.
* Open the TinglingGit Directory in terminal and install dependancies.<br>
  ` pip install -r requirements.txt `
* Configure github settings by creating a personal access token at https://github.com/settings/tokens and adding it to tinglinggit.ini. Note that no special scope privileges are required by TinglingGit.
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
* We can also list Stale issues by using `--stale-issues` as a argument paramater.<br>
  ` python /path/to/TinglingGit/analyse-files.py --stale-issues`
* The date older then which the issues should be considered stale could be specified by using `--older-then` argument.<br>
  ` python /path/to/TinglingGit/analyse-files.py --stale-issues --older-then 20170128`<br>
  This will list all issues which are updated before 28-01-2017.
* We can also filter the issues based on labels defined in the repository.<br>
  ` python /path/to/TinglingGit/analyse-files.py --stale-issues --labels 'area: tooling'`
* A combination could be used as follows<br>
  ` python /path/to/TinglingGit/analyse-files.py --stale-issues --older-then 20170128 --labels 'area: tooling'`

# Example output

Below is example final output from running the tool.  The files in the
top list are ones where there are no open PRs touching those files.

They are followed by all the files that do have open PRs touching
those files, with the diffstats of the PRs changes to those files.


```
~/zulip/zerver/views$ python ~/TinglingGit/analyse-files.py
Fetching Diffs Completed
zerver/__init__.py
zerver/__init__.pyc
zerver/filters.py
zerver/logging_handlers.py
zerver/signals.py
zerver/static_header.txt
zerver/storage.py
zerver/apps.py [PR#5224(+1-1)](https://github.com/zulip/zulip/pull/5224)
zerver/context_processors.py
[PR#5753(+1-0)](https://github.com/zulip/zulip/pull/5753)
[PR#7234(+2-0)](https://github.com/zulip/zulip/pull/7234)
[PR#7038(+20-0)](https://github.com/zulip/zulip/pull/7038)
zerver/decorator.py
[PR#5753(+24-0)](https://github.com/zulip/zulip/pull/5753)
[PR#5880(+60-39)](https://github.com/zulip/zulip/pull/5880)
[PR#6086(+21-21)](https://github.com/zulip/zulip/pull/6086)
[PR#6737(+3-2)](https://github.com/zulip/zulip/pull/6737)
zerver/forms.py
[PR#7437(+51-57)](https://github.com/zulip/zulip/pull/7437)
[PR#5753(+20-0)](https://github.com/zulip/zulip/pull/5753)
[PR#7027(+3-3)](https://github.com/zulip/zulip/pull/7027)
[PR#6084(+36-0)](https://github.com/zulip/zulip/pull/6084)
[PR#6086(+1-1)](https://github.com/zulip/zulip/pull/6086)
zerver/middleware.py
[PR#5880(+60-18)](https://github.com/zulip/zulip/pull/5880)
[PR#7427(+2-0)](https://github.com/zulip/zulip/pull/7427)
[PR#6086(+2-2)](https://github.com/zulip/zulip/pull/6086)
zerver/models.py
[PR#5633(+28-1)](https://github.com/zulip/zulip/pull/5633)
[PR#4110(+4-4)](https://github.com/zulip/zulip/pull/4110)
[PR#5665(+20-0)](https://github.com/zulip/zulip/pull/5665)
[PR#6492(+2-0)](https://github.com/zulip/zulip/pull/6492)
[PR#6705(+8-0)](https://github.com/zulip/zulip/pull/6705)
[PR#6199(+8-0)](https://github.com/zulip/zulip/pull/6199)
[PR#5224(+2-3)](https://github.com/zulip/zulip/pull/5224)...
```
