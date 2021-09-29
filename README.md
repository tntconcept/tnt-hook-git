# TNT Git Hook

This is a simple, per project, Git pre push hook, so when you push your commits an auto evidence is created in the associated TNT project.

**If you use this hook you DO NOT NEED to add manualy a photo as evidence!**


### Install

Requirements:
- Python 3.7
- pip3

To check if is already installed in your system you can try to run in the command line: `pip3 --version`

If you need to install them, both can be obtained from python.org or with [homebrew](https://brew.sh/) (recommended!): `brew install python3`

Autentia private Nexus Pypi (package repository) must be added. Edit (or create if needed) the file `~/.config/pip.conf`

```
[global]
index = https://pypi.python.org/pypi/
index-url = https://pypi.python.org/simple/
extra-index-url = https://tnt.autentia.com/nexus/repository/autentia-pypi/simple/
trusted-host = tnt.autentia.com
```

To check the file is properly configured run 

`python3 -m pip config list`

And it should show something like this

```
global.extra-index-url='https://tnt.autentia.com/nexus/repository/autentia-pypi/simple/'
global.index='https://pypi.python.org/pypi/'
global.index-url='https://pypi.python.org/simple/'
global.trusted-host='tnt.autentia.com'
```

if this is not working, place the file in `~/.pip/pip.conf`

To install or upgrade the TNTGitHook utility run the following command:

```bash
python3 -m pip install --upgrade TNTGitHook --user
```


#### Credentials

Once everything is installed, in order to set TNT login credentials, use the following command:

```bash
python3 -m TNTGitHook --set-credentials
```

Credentials will be secured using system APIs, keychain in macOS, several options on Linux depending on desktop, and whatever security Windows may have. Check https://pypi.org/project/keyring/ for more detail


### Usage

Once utility is installed, in order to auto imputate on each git push, you must setup the tool by using this command on the root of your git repository.

**This configuration is per git repository!**

```bash
python3 -m TNTGitHook --setup
```

It will prompt you for the organization, project and role names (they must match exactly with the ones on TNT, otherwise tool will complain).


### Manual Setup

**Notice: This is what _TNTGitHook --setup_ does under the hood, so you can skip this section.**

Create the following script on `<your-git-project>/.git/hooks/pre-push`

```bash
#!/bin/bash
set -o pipefail

read local_ref local_sha remote_ref remote_sha
PROJECT_PATH=$(git rev-parse --show-toplevel)
# Assumes tnt_git_hook.sh is on PATH
tnt_git_hook $local_ref $local_sha $remote_ref $remote_sha $PROJECT_PATH
```

And give it execution permission:

```bash
chmod +x .git/hooks/pre-push
```

Also create a file **.git/hooks/TNTGitHookConfig.json** to indicate to which project impute. Double check that the information is as showed in TNT. Example:

```json
{
    "organization": "Some organization",
    "project": "Project",
    "role": "Role"
}
```

Create this script in `/usr/local/bin/tnt_git_hook.sh`
```bash
#!/bin/bash
set -o pipefail

local_ref=$1
local_sha=$2
remote_ref=$3
remote_sha=$4
PROJECT_PATH=$5
CURRENT_PATH=$(pwd)

cd $PROJECT_PATH||exit 1
if [ -n "$local_sha" ] && [ -n "$remote_sha" ] && [ $((16#$local_sha)) -ne 0 ]
then
  CMD='git log --pretty="format:%H;%aI;%an <%ae>;%s"'
  if [ $((16#$remote_sha)) -ne 0 ]
  then
    CMD="$CMD $remote_sha..$local_sha"
  else
# Remote being created or deleted. For complete information view: https://www.git-scm.com/docs/githooks#_pre_push
# We are going to retrieve the commits only accessible from the current branch (local_ref)
    CMD="$CMD $local_ref --not $(git for-each-ref --format='%(refname)' refs/heads/ | grep -v "refs/heads/$local_ref")"
  fi
  CMD="$CMD 2> /dev/null"
  FILENAME="/tmp/tnt-git-hook-commits-$(date +%s)"
  eval $CMD > $FILENAME

  # Do nothing on error, just inform and go ahead with "git push" (i.e. conflicts)
  if [ $? -ne 0 ]
  then
    echo "Unable to retrieve git log information, will not create evidence on TNT but push continues"
    rm $FILENAME
    cd $CURRENT_PATH || exit 0
    exit 0
  fi

  REMOTE=$(git ls-remote --get-url | head -1)

  if ! python3 -m TNTGitHook --commit-msgs-file $FILENAME --remote $REMOTE;
  then
    echo "Error executing python hook"
    exit 1
  fi
  rm $FILENAME
fi
cd $CURRENT_PATH || exit 0
```

And give it execution permission:

```bash
chmod +x /usr/local/bin/tnt_git_hook.sh
```
### Build release 

To build Pypi, modify setup.py accordingly (versions, name, etc) package.
Verify that you don't have old execution folders:
* build/
* dist/
* TNTGitHook.egg-info/

Then execute

```bash
python3 setup.py sdist bdist_wheel
```

To upload to Nexus (you'll need to have twine installed: `pip3 install twine`):

```bash
python3 -m twine upload --repository-url https://tnt.autentia.com/nexus/repository/autentia-pypi/ dist/*
```

If the process fails with this error:
```bash
HTTPError: 400 Bad Request from https://tnt.autentia.com/nexus/repository/autentia-pypi/
Repository does not allow updating assets: autentia-pypi
```
check that you don't have old artifacts in `dist` folder. In that case, delete accordingly.
