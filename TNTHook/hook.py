from __future__ import annotations

import json
from datetime import timedelta
from typing import List

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


def create_activity(config: Config,
                    organization_name: str,
                    project_name: str,
                    role_name: str,
                    billable: bool,
                    commit_msgs: str):
    headers = {"Authorization": "Basic dG50LWNsaWVudDpob2xh"}
    payload = {"grant_type": "password",
               "username": "testuser",
               "password": "holahola"}
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


    # start = date.today().replace(day=1)
    # next_month = calendar.nextmonth(start.year, start.month)
    # end = start.replace(year=next_month[0], month=next_month[1])
    # params = {"startDate": start, "endDate": end}
    # response: Response = requests.get(config.baseURL + "activities", headers=headers, params=params)
    # print(response.json())
    info: (str, datetime, int) = generate_info(commit_msgs)

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


def generate_info(commit_msgs: str) -> (str, datetime, int):
    def msg_parser(msg: str) -> (str, datetime, int):
        result = msg.split(";")
        result[2] = datetime.fromisoformat(result[2])
        return result

    msgs = commit_msgs.split("\n")
    msgs: [(str, datetime, int)] = list(map(msg_parser, msgs))
    first_msg = msgs[0]
    last_msg = msgs[-1]

    start_date: datetime = first_msg[2]
    end_date: datetime = last_msg[2]

    duration: timedelta = start_date - end_date

    result_str: str = "--Autocreated activity--"
    result_str += "\n".join(map(lambda m: "SHA: " + m[0] + "\nMessage: " + m[1] + "\n-----", msgs))
    return result_str, start_date, duration.total_seconds() / 60
