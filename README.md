To build Pypi package run
```
python3 setup.py sdist bdist_wheel
```
To upload to nexus:
```
python3 -m twine upload --repository-url https://autentia.no-ip.org/nexus/repository/autentia-pypi/ dist/*
```