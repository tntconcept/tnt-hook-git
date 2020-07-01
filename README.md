# TNT Hook

### Build release 
To build Pypi package run
```shell script
python3 setup.py sdist bdist_wheel
```
To upload to nexus:
```shell script
python3 -m twine upload --repository-url https://autentia.no-ip.org/nexus/repository/autentia-pypi/ dist/*
```

### Install
Requirements:
- Python 3.7
- pip3

Both can be obtained from python.org or with homebrew.

Autentia private nexus Pypi repository must be added. Edit (or create if needed) the file ```~/.pip/pip.conf```
```
[global]
index = https://pypi.python.org/pypi/
index-url=https://pypi.python.org/simple/
extra-index-url=https://autentia.no-ip.org/nexus/repository/autentia-pypi/simple/
trusted-host = autentia.no-ip.org
```

To install or upgrade the TNTHook utility run the following command:
```shell script
pip3 install --upgrade TNTHook
```

### Usage
Once utility is installed, in order to auto imputate on each git push, create the following script on <your-git-project>/.git/hooks/pre-push
```shell script
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

  # Assumes TNTHook is on PATH
  TNTHook --commit-msgs "$MSGS" --remote $REMOTE
fi
```
And give it execution permission:
```bash
chmod +x .git/hooks/pre-push
```
Also create a file **.git/hooks/tnthookconfig.json** to indicate to which proyect imputate. Example:
```json
{
    "organization": "Some organization",
    "project": "Project",
    "role": "Role",
}
```
Once everything is set up, in order to set TNT login credentials, use the following command:
```shell script
TNTHook --set-credentials
```
Credentials will be secured using system APIs, keychain in macOS, several options on linux depending on desktop, and whatever security windows may have. Check https://pypi.org/project/keyring/ for more detail
