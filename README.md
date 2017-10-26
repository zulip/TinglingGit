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
zerver/views/email_mirror.py
zerver/views/pointer.py
zerver/views/realm_domains.py
zerver/views/push_notifications.py
zerver/views/muting.py
zerver/views/tutorial.py
zerver/views/realm_filters.py
zerver/views/hotspots.py
zerver/views/report.py
zerver/views/realm_emoji.py
zerver/views/unsubscribe.py
zerver/views/typing.py
zerver/views/compatibility.py
zerver/views/alert_words.py
zerver/views/custom_profile_fields.py
zerver/views/zephyr.py
zerver/views/presence.py
zerver/views/realm_icon.py
zerver/views/events_register.py
zerver/views/invite.py
[PR#6607(+2-2)](git@github.com:zulip/zulip/pull/6607)
[PR#6931(+36-4)](git@github.com:zulip/zulip/pull/6931)
[PR#7015(+7-3)](git@github.com:zulip/zulip/pull/7015)
zerver/views/messages.py
[PR#4110(+1-1)](git@github.com:zulip/zulip/pull/4110)
[PR#6492(+13-2)](git@github.com:zulip/zulip/pull/6492)
[PR#4177(+3-0)](git@github.com:zulip/zulip/pull/4177)
[PR#6607(+1-1)](git@github.com:zulip/zulip/pull/6607)
[PR#6017(+1-1)](git@github.com:zulip/zulip/pull/6017)
[PR#6573(+13-2)](git@github.com:zulip/zulip/pull/6573)
[PR#7112(+3-3)](git@github.com:zulip/zulip/pull/7112)
zerver/views/email_log.py
[PR#7142(+18-1)](git@github.com:zulip/zulip/pull/7142)
zerver/views/realm.py
[PR#6492(+13-5)](git@github.com:zulip/zulip/pull/6492)
[PR#6705(+12-2)](git@github.com:zulip/zulip/pull/6705)
[PR#3382(+1-0)](git@github.com:zulip/zulip/pull/3382)
[PR#4586(+3-0)](git@github.com:zulip/zulip/pull/4586)
zerver/views/home.py
[PR#5753(+11-1)](git@github.com:zulip/zulip/pull/5753)
[PR#3317(+1-0)](git@github.com:zulip/zulip/pull/3317)
[PR#4452(+5-12)](git@github.com:zulip/zulip/pull/4452)
[PR#7036(+29-3)](git@github.com:zulip/zulip/pull/7036)
[PR#5525(+1-0)](git@github.com:zulip/zulip/pull/5525)
zerver/views/__init__.py
[PR#388(+21-0)](git@github.com:zulip/zulip/pull/388)
zerver/views/streams.py
[PR#6199(+1-0)](git@github.com:zulip/zulip/pull/6199)
[PR#6607(+8-8)](git@github.com:zulip/zulip/pull/6607)
[PR#6973(+31-1)](git@github.com:zulip/zulip/pull/6973)
[PR#1432(+13-2)](git@github.com:zulip/zulip/pull/1432)
[PR#2984(+11-2)](git@github.com:zulip/zulip/pull/2984)
[PR#6573(+1-1)](git@github.com:zulip/zulip/pull/6573)
zerver/views/users.py
[PR#5633(+5-1)](git@github.com:zulip/zulip/pull/5633)
[PR#5665(+18-6)](git@github.com:zulip/zulip/pull/5665)
[PR#6607(+3-2)](git@github.com:zulip/zulip/pull/6607)
[PR#3317(+21-1)](git@github.com:zulip/zulip/pull/3317)
[PR#6927(+1-0)](git@github.com:zulip/zulip/pull/6927)
[PR#5962(+14-2)](git@github.com:zulip/zulip/pull/5962)
[PR#7020(+2-2)](git@github.com:zulip/zulip/pull/7020)
[PR#7159(+6-6)](git@github.com:zulip/zulip/pull/7159)
zerver/views/reactions.py
[PR#7026(+63-4)](git@github.com:zulip/zulip/pull/7026)
zerver/views/auth.py
[PR#5753(+88-15)](git@github.com:zulip/zulip/pull/5753)
[PR#5880(+12-2)](git@github.com:zulip/zulip/pull/5880)
[PR#7027(+23-16)](git@github.com:zulip/zulip/pull/7027)
zerver/views/attachments.py
[PR#6859(+2-0)](git@github.com:zulip/zulip/pull/6859)
zerver/views/upload.py
[PR#6859(+6-0)](git@github.com:zulip/zulip/pull/6859)
[PR#4387(+2-7)](git@github.com:zulip/zulip/pull/4387)
zerver/views/user_settings.py
[PR#6199(+3-1)](git@github.com:zulip/zulip/pull/6199)
[PR#5753(+3-1)](git@github.com:zulip/zulip/pull/5753)
[PR#5880(+3-1)](git@github.com:zulip/zulip/pull/5880)
[PR#7027(+3-0)](git@github.com:zulip/zulip/pull/7027)
[PR#5573(+2-1)](git@github.com:zulip/zulip/pull/5573)
[PR#7147(+3-1)](git@github.com:zulip/zulip/pull/7147)
zerver/views/integrations.py
[PR#5901(+4-5)](git@github.com:zulip/zulip/pull/5901)
[PR#7116(+1-0)](git@github.com:zulip/zulip/pull/7116)
zerver/views/registration.py
[PR#6255(+1-3)](git@github.com:zulip/zulip/pull/6255)
[PR#5880(+1-0)](git@github.com:zulip/zulip/pull/5880)
[PR#6973(+5-2)](git@github.com:zulip/zulip/pull/6973)
[PR#7015(+3-1)](git@github.com:zulip/zulip/pull/7015)
[PR#7027(+26-21)](git@github.com:zulip/zulip/pull/7027)
```

