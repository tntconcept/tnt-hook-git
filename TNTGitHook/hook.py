from __future__ import annotations

import json
import os
from datetime import timedelta, datetime
from functools import reduce
from getpass import getpass
from typing import List, Tuple

import keyring
import requests
from requests import Response
import stat
import importlib.resources as pkg_resources

from TNTGitHook.entities import *
from TNTGitHook.exceptions import NoCredentialsError, AuthError, NotFoundError
from TNTGitHook.utils import DateTimeEncoder, first, to_class

NAME: str = "TNTGitHook"
DEFAULT_CONFIG_FILE_PATH: str = f".git/hooks/{NAME}Config.json"


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
            return Config(baseURL="https://tnt.autentia.com/tntconcept-api-rest-kotlin/api/",
                          authURL="https://tnt.autentia.com/tntconcept-api-rest-kotlin/oauth/token",
                          basic_auth="dG50LWNsaWVudDpDbGllbnQtVE5ULXYx")


class PrjConfig:
    organization: str
    project: str
    role: str
    ignore_errors: bool = False

    @staticmethod
    def activity_prefix() -> str:
        return "###Autocreated evidence###\n(DO NOT DELETE)"


def ask_credentials():
    keyring.set_password(f"com.autentia.{NAME}", "username", input("User: "))
    keyring.set_password(f"com.autentia.{NAME}", "password", getpass())


def setup(config: Config):
    with pkg_resources.path(NAME, "misc") as context:
        script = (context / "pre-push.sh").read_text()
        try:
            path = ".git/hooks/pre-push"
            with open(path, "w") as f:
                f.write(script)
                st = os.stat(path)
                os.chmod(path, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

            headers = generate_request_headers(config)
            organization = check_organization_exists(config, headers, input("Organization: "))
            project = check_project_exists(config, headers, organization, input("Project: "))
            role = check_role_exists(config, headers, project, input("Role: "))

            path = DEFAULT_CONFIG_FILE_PATH
            prj_config = PrjConfig()
            prj_config.organization = organization.name
            prj_config.project = project.name
            prj_config.role = role.name

            with open(path, "w") as f:
                f.write(json.dumps(prj_config.__dict__, sort_keys=True, indent=4))
        except FileNotFoundError:
            print("Unable to setup hook. Is this a git repository?")
        except Exception as ex:
            print(ex)


def create_activity(config: Config,
                    prj_config: PrjConfig,
                    commit_msgs: str,
                    remote: str):
    organization_name = prj_config.organization
    project_name = prj_config.project
    role_name = prj_config.role
    billable = False

    headers = generate_request_headers(config)

    organization = check_organization_exists(config, headers, organization_name)

    project = check_project_exists(config, headers, organization, project_name)

    role = check_role_exists(config, headers, project, role_name)

    now = datetime.now()
    now = now.strftime("%Y-%m-%d")
    response: Response = requests.get(config.baseURL + "activities/",
                                      params={"startDate": str(now), "endDate": str(now)},
                                      headers=headers,
                                      timeout=5)
    activities_response: List[ActivitiesResponse]
    activities_response = json.loads(response.text, object_hook=lambda x: to_class(x, cls=ActivitiesResponse))
    activities = reduce(lambda r, a: r + a.activities, activities_response, [])
    existing_activity = first(lambda a: PrjConfig.activity_prefix() in a.description, activities)

    info: (str, datetime, int) = generate_info(commit_msgs,
                                               existing_activity,
                                               remote_url=remote)

    new_activity: CreateActivityRequest = CreateActivityRequest()
    if existing_activity is not None:
        new_activity.id = existing_activity.id
    new_activity.description = info[0]
    new_activity.startDate = info[1]
    new_activity.duration = 0
    new_activity.billable = billable
    new_activity.projectRoleId = role.id

    json_str = json.dumps(new_activity.__dict__, cls=DateTimeEncoder)
    data = json.loads(json_str)

    response: Response = requests.post(config.baseURL + "activities?autotruncate",
                                       headers=headers,
                                       json=data,
                                       timeout=5)
    if response.status_code == 200:
        print("Successfully created activity for " + project_name + " - " + role_name)


def generate_request_headers(config):
    username = keyring.get_password(f"com.autentia.{NAME}", "username")
    password = keyring.get_password(f"com.autentia.{NAME}", "password")
    if not username or not password:
        raise NoCredentialsError()
    headers = {"Authorization": "Basic " + config.basic_auth}
    payload = {"grant_type": "password",
               "username": username,
               "password": password}
    token_response = requests.post(config.authURL, headers=headers, data=payload, timeout=5)
    if token_response.status_code != 200:
        raise AuthError()
    access_token = token_response.json()["access_token"]
    headers = {"Authorization": "Bearer " + access_token}
    return headers


def check_role_exists(config, headers, project, role_name):
    response: Response = requests.get(config.baseURL + "projects/" + str(project.id) + "/roles",
                                      headers=headers, timeout=5)
    response.encoding = 'utf-8'
    roles: List[Role] = json.loads(response.text, object_hook=lambda x: to_class(x, cls=Role))
    role = first(lambda r: r.name == role_name, roles)
    if not role:
        raise NotFoundError("Role", role_name)
    return role


def check_project_exists(config, headers, organization, project_name):
    response: Response = requests.get(config.baseURL + "organizations/" + str(organization.id) + "/projects",
                                      headers=headers, timeout=5)
    response.encoding = 'utf-8'
    projects: List[Project] = json.loads(response.text, object_hook=lambda x: to_class(x, cls=Project))
    project = first(lambda p: p.name == project_name, projects)
    if not project:
        raise NotFoundError("Project", project_name)
    return project


def check_organization_exists(config, headers, organization_name):
    response: Response = requests.get(config.baseURL + "organizations", headers=headers, timeout=5)
    response.encoding = 'utf-8'
    organizations: List[Organization] = json.loads(response.text, object_hook=lambda x: to_class(x, cls=Organization))
    organization = first(lambda o: o.name == organization_name, organizations)
    if not organization:
        raise NotFoundError("Organization", organization_name)
    return organization


def generate_info(commit_msgs: str,
                  existing_activity: Activity = None,
                  remote_url: str = None) -> (str, datetime):
    prefix = PrjConfig.activity_prefix()

    def msg_parser(msg: str) -> Tuple[str, str, str, str]:
        items = msg.split(";")
        # return items[0], items[1], items[2]
        return items[0], items[1], items[2], items[3]

    lines = commit_msgs.split("\n")[::-1]
    msgs: [Tuple[str, str, datetime, str]] = list(map(msg_parser, lines))

    start_date: datetime = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0, tzinfo=None)

    remote_url = "" if remote_url is None else remote_url + "\n"
    result_str: str = prefix + "\n"
    previous_descriptions: str = ""
    if existing_activity is not None:
        previous_descriptions = existing_activity.description \
            .replace(result_str, "") \
            .replace(remote_url, "")
        previous_descriptions += "\n-----\n"
    result_str += remote_url
    result_str += previous_descriptions
    result_str += "\n-----\n".join(map(lambda m: "\n".join(m), msgs))

    return result_str, start_date
