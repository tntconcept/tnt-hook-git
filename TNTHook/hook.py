from __future__ import annotations

import json
from datetime import timedelta, datetime
from getpass import getpass
from typing import List, Tuple

import keyring
import requests
from requests import Response

from TNTHook.entities import *
from TNTHook.utils import DateTimeEncoder, first, to_class


class Config:
    baseURL: str
    authURL: str

    def __init__(self, baseURL: str, authURL: str):
        self.baseURL = baseURL
        self.authURL = authURL

    @staticmethod
    def config(debug: bool) -> Config:
        if debug:
            return Config(baseURL="http://localhost:8080/api/",
                          authURL="http://localhost:8080/oauth/token")
        else:
            # TODO: Change this
            return Config(baseURL="http://localhost:8080/api/",
                          authURL="http://localhost:8080/oauth/token")


def ask_credentials():
    keyring.set_password("com.autentia.TNTHook", "username", input("User: "))
    keyring.set_password("com.autentia.TNTHook", "password", getpass())


def create_activity(config: Config,
                    organization_name: str,
                    project_name: str,
                    role_name: str,
                    billable: bool,
                    commit_msgs: str,
                    prev_commit_date_str: str):

    username = keyring.get_password("com.autentia.TNTHook", "username")
    password = keyring.get_password("com.autentia.TNTHook", "password")

    if not username or not password:
        raise Exception('No credentials')

    headers = {"Authorization": "Basic dG50LWNsaWVudDpob2xh"}
    payload = {"grant_type": "password",
               "username": username,
               "password": password}
    token_response = requests.post(config.authURL, headers=headers, data=payload)
    access_token = token_response.json()["access_token"]

    headers = {"Authorization": "Bearer " + access_token}

    response: Response = requests.get(config.baseURL + "organizations", headers=headers)
    organizations: List[Organization] = json.loads(response.text, object_hook=lambda x: to_class(x, cls=Organization))

    organization = first(lambda o: o.name == organization_name, organizations)
    if not organization:
        raise Exception('Not found', organization_name)

    response: Response = requests.get(config.baseURL + "organizations/" + str(organization.id) + "/projects",
                                      headers=headers)
    projects: List[Project] = json.loads(response.text, object_hook=lambda x: to_class(x, cls=Project))
    project = first(lambda p: p.name == project_name, projects)

    if not project:
        raise Exception('Not found', project_name)

    response: Response = requests.get(config.baseURL + "projects/" + str(project.id) + "/roles",
                                      headers=headers)
    roles: List[Role] = json.loads(response.text, object_hook=lambda x: to_class(x, cls=Role))
    role = first(lambda r: r.name == role_name, roles)

    if not role:
        raise Exception('Not found', role_name)

    prev_commit_date = datetime.fromisoformat(prev_commit_date_str) if prev_commit_date_str else None

    info: (str, datetime, int) = generate_info(commit_msgs,
                                               prev_commit_date=prev_commit_date)

    new_activity: CreateActivityRequest = CreateActivityRequest()
    new_activity.description = info[0]
    new_activity.startDate = info[1]
    new_activity.duration = info[2]
    new_activity.billable = billable
    new_activity.projectRoleId = role.id

    json_str = json.dumps(new_activity.__dict__, cls=DateTimeEncoder)
    data = json.loads(json_str)

    response: Response = requests.post(config.baseURL + "activities", headers=headers, json=data)
    print(response.status_code)


def generate_info(commit_msgs: str, prev_commit_date: datetime) -> (str, datetime, int):
    def msg_parser(msg: str) -> Tuple[str, str, datetime]:
        result = msg.split(";")
        result[2] = datetime.fromisoformat(result[2])
        return result

    lines = commit_msgs.split("\n")
    msgs: [Tuple[str, str, datetime]] = list(map(msg_parser, lines))
    first_msg = msgs[0]
    last_msg = msgs[-1]

    start_date: datetime = prev_commit_date or first_msg[2]
    end_date: datetime = last_msg[2]

    duration: timedelta = end_date - start_date

    result_str: str = "--Autocreated activity--\n"
    result_str += "\n-----\n".join(map(lambda m: "SHA: " + m[0] + "\nMessage: " + m[1], msgs))
    return result_str, start_date, duration.total_seconds() / 60
