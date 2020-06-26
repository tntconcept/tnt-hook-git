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
    basic_auth: str

    def __init__(self, baseURL: str, authURL: str, basic_auth: str):
        self.baseURL = baseURL
        self.authURL = authURL
        self.basic_auth = basic_auth

    @staticmethod
    def config(debug: bool) -> Config:
        if debug:
            return Config(baseURL="http://localhost:8080/api/",
                          authURL="http://localhost:8080/oauth/token",
                          basic_auth="dG50LWNsaWVudDpob2xh")
        else:
            # TODO: Change this
            return Config(baseURL="https://autentia.no-ip.org/tntconcept-api-rest-kotlin/api/",
                          authURL="https://autentia.no-ip.org/tntconcept-api-rest-kotlin/oauth/token",
                          basic_auth="dG50LWNsaWVudDpDbGllbnQtVE5ULXYx")


class PrjConfig:
    organization: str
    project: str
    role: str
    billable: bool = False
    activity_prefix: str = None


def ask_credentials():
    keyring.set_password("com.autentia.TNTHook", "username", input("User: "))
    keyring.set_password("com.autentia.TNTHook", "password", getpass())


def create_activity(config: Config,
                    prj_config: PrjConfig,
                    commit_msgs: str,
                    prev_commit_date_str: str,
                    remote: str):
    organization_name = prj_config.organization
    project_name = prj_config.project
    role_name = prj_config.role
    billable = prj_config.billable

    username = keyring.get_password("com.autentia.TNTHook", "username")
    password = keyring.get_password("com.autentia.TNTHook", "password")

    if not username or not password:
        raise Exception('No credentials')

    headers = {"Authorization": "Basic " + config.basic_auth}
    payload = {"grant_type": "password",
               "username": username,
               "password": password}
    token_response = requests.post(config.authURL, headers=headers, data=payload)
    if token_response.status_code != 200:
        raise Exception("Authentication failed")
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
                                               prev_commit_date=prev_commit_date,
                                               prefix=prj_config.activity_prefix,
                                               remote_url=remote)

    new_activity: CreateActivityRequest = CreateActivityRequest()
    new_activity.description = info[0]
    new_activity.startDate = info[1]
    new_activity.duration = info[2]
    new_activity.billable = billable
    new_activity.projectRoleId = role.id

    json_str = json.dumps(new_activity.__dict__, cls=DateTimeEncoder)
    data = json.loads(json_str)

    response: Response = requests.post(config.baseURL + "activities", headers=headers, json=data)
    if response.status_code == 200:
        print("Successfully created activity for " + project_name + " - " + role_name)


def generate_info(commit_msgs: str,
                  prev_commit_date: datetime,
                  prefix: str = None,
                  remote_url: str = None) -> (str, datetime, int):
    prefix = prefix if prefix is not None else "--Autocreated activity--"
    if remote_url is not None:
        prefix += "\n" + remote_url

    # Rounds time to quarter periods and remove timezone info
    def adjust_time(time: datetime) -> datetime:
        # if activity was started previous day, "adjust" it to current push date at 8AM
        today = datetime.now()
        if time.day < today.day:
            time = today.replace(hour=8, minute=0)
        minute = time.minute
        minute = int(minute / 15) * 15
        return time.replace(minute=minute, second=0, microsecond=0, tzinfo=None)

    def msg_parser(msg: str) -> Tuple[str, str, datetime]:
        items = msg.split(";")
        date = datetime.fromisoformat(items[2])
        return items[0], items[1], adjust_time(date)

    lines = commit_msgs.split("\n")
    msgs: [Tuple[str, str, datetime]] = list(map(msg_parser, lines))
    first_msg = msgs[0]
    last_msg = msgs[-1]

    start_date: datetime = adjust_time(prev_commit_date or first_msg[2])
    end_date: datetime = last_msg[2]

    duration: timedelta = end_date - start_date

    result_str: str = prefix + "\n"
    result_str += "\n-----\n".join(map(lambda m: "SHA: " + m[0] + "\nMessage: " + m[1], msgs))
    return result_str, start_date, max(duration.total_seconds() / 60,15)
