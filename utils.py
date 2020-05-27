import inspect
import json
from datetime import datetime
from typing import Any, cast, Iterable, Callable, TypeVar

from entities import Organization, Project


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
