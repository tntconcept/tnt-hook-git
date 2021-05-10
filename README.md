# TNT Git Hook

This is a simple, per project, Git pre push hook, so when you push your commits an auto evidence is created in the asociated TNT project.

**If you use this hook you DO NOT NEED to add manualy a photo as evidence!**


### Install

Requirements:
- Python 3.7
- pip3

To check if is alredy installed in your sistem you can try to run in the command line: `pip3 --version`

If you need to install them, both can be obtained from python.org or with [homebrew](https://brew.sh/) (recomended!): `brew install python3`

Autentia private Nexus Pypi (package repository) must be added. Edit (or create if needed) the file `~/.pip/pip.conf`

```
[global]
index = https://pypi.python.org/pypi/
index-url = https://pypi.python.org/simple/
extra-index-url = https://tnt.autentia.com/nexus/repository/autentia-pypi/simple/
trusted-host = tnt.autentia.com
```

To install or upgrade the TNTGitHook utility run the following command:

```bash
pip3 install --upgrade TNTGitHook
```


#### Credentials

Once everything is installed, in order to set TNT login credentials, use the following command:

```bash
TNTGitHook --set-credentials
```

Credentials will be secured using system APIs, keychain in macOS, several options on Linux depending on desktop, and whatever security Windows may have. Check https://pypi.org/project/keyring/ for more detail


### Usage

Once utility is installed, in order to auto imputate on each git push, you must setup the tool by using this command on the root of your git repository.

**This configuration is per git repository!**

```bash
TNTGitHook --setup
```

It will prompt you for the organization, project and role names (they must match exactly with the ones on TNT, otherwise tool will complain).


### Manual Setup

**Notice: This is what _TNTGitHook --setup_ does under the hood, so you can skip this section.**

Create the following script on `<your-git-project>/.git/hooks/pre-push`

```bash
#!/bin/bash

read local_ref local_sha remote_ref remote_sha

if [ -n "$local_sha" ] && [ -n "$remote_sha" ]
then
  if [ $((16#$remote_sha)) -eq 0 ]
  then
    MSGS=`git log --pretty="format:%H;%aI;%an <%ae>;%s"`
  else
    MSGS=`git log --pretty="format:%H;%aI;%an <%ae>;%s" $remote_sha..$local_sha`
  fi
  REMOTE=`git ls-remote --get-url | head -1`

  # Assumes TNTGitHook is on PATH
  TNTGitHook --commit-msgs "$MSGS" --remote $REMOTE
fi
```

And give it execution permission:

```bash
chmod +x .git/hooks/pre-push
```

Also create a file **.git/hooks/TNTGitHookConfig.json** to indicate to which project imputate. Example:

```json
{
    "organization": "Some organization",
    "project": "Project",
    "role": "Role"
}
```


### Build release 

To build Pypi, modify setup.py accordingly (versions, name, etc) package run

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
