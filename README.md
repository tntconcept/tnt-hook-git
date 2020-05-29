To build Pypi package run
```
python3 setup.py sdist bdist_wheel
```
To upload to nexus:
```
python3 -m twine upload --repository-url https://autentia.no-ip.org/nexus/repository/autentia-pypi/ dist/*
```

In order to set TNT login credentials, use the following command:
To upload to nexus:
```
TNTHook --set-credentials
```