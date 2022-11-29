import json
import re
from datetime import datetime
from typing import Any, Iterable, Callable, TypeVar

from TNTGitHook.entities import Organization


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)


class OrganizationListDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        result = Organization()
        result.__dict__.update(obj)
        return result


T = TypeVar('T')


def to_class(obj: dict, cls: T) -> T:
    result = cls()
    result.__dict__.update(obj)
    return result


def first(function: Callable[[T], bool], iterable: Iterable[T]) -> T:
    for item in iterable:
        if function(item):
            return item

def formatRemoteURL(remoteURL) -> str:

    userPattern = "\/+\w.*\:"
    tokenPattern = "\:+([\w\d]*)@"

    if(remoteURL is None):
        return remoteURL

    user = re.search(userPattern, remoteURL)

    if(user is None):
        return remoteURL

    user = user.group(0)
    formattedURL = re.sub(user, "//****:", remoteURL)
    token = re.search(tokenPattern, formattedURL).group(1)
    formattedURL = re.sub(token, "****", formattedURL)

    return formattedURL
