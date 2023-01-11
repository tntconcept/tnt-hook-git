from __future__ import annotations

import hashlib
import json
import os
import pkgutil
from functools import reduce
from typing import List, Tuple

import keyring
import requests
from keyring.errors import PasswordDeleteError
from requests import Response
import stat

from TNTGitHook.entities import *
from TNTGitHook.exceptions import NoCredentialsError, AuthError, NotFoundError, NetworkError, EmptyCommitMessagesFileError, CommitMessagesFileNotFoundError
from TNTGitHook.utils import DateTimeEncoder, first, to_class, formatRemoteURL

NAME: str = "TNTGitHook"
DEFAULT_CONFIG_FILE_PATH: str = f".git/hooks/{NAME}Config.json"
# In fact is 2048, but as we are going to substitute the last characters for \n... we need 5 empty at the end
TNT_DESCRIPTION_MAX_SIZE = 2043


class Config:
    baseURL: str
    authURL: str
    basic_auth: str
    timeout: int = 5

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
    timeout: int = 5

    @staticmethod
    def activity_prefix() -> str:
        return "###Autocreated evidence###\n(DO NOT DELETE)"


def setup_config(config:Config, selected_organization:str, selected_project:str, selected_role:str):
    if selected_organization == "":
        selected_organization = input("Organization: ")

    if selected_project == "":
        selected_project = input("Project: ")

    if selected_role == "":
        selected_role = input("Role: ")

    try:
        headers = generate_request_headers(config)
        organization = check_organization_exists(config, headers, selected_organization)
        project = check_project_exists(config, headers, organization, selected_project)
        role = check_role_exists(config, headers, project, selected_role)

        path = DEFAULT_CONFIG_FILE_PATH
        prj_config = PrjConfig()
        prj_config.organization = organization.name
        prj_config.project = project.name
        prj_config.role = role.name

        with open(path, "w") as f:
            f.write(json.dumps(prj_config.__dict__, sort_keys=True, indent=4))
    except FileNotFoundError:
        print("Unable to setup config. Is this a git repository?\nMaybe you're not at the root folder.")
    except Exception as ex:
        print(ex)


def write_hook_script():
    hook_script = pkgutil.get_data('TNTGitHook', 'misc/tnt_git_hook.sh').decode('utf8')
    try:
        path = f"/usr/local/bin/tnt_git_hook"
        with open(path, "w") as file:
            file.write(hook_script)
            stats = os.stat(path)
            os.chmod(path, stats.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except FileNotFoundError:
        print(f"Unable to setup hook script. Are you able to write to /usr/local/bin?")
    except Exception as ex:
        print(ex)


def get_hook_sha1():
    hook_script = pkgutil.get_data('TNTGitHook', 'misc/tnt_git_hook.sh').decode('utf8')
    return hashlib.sha1(hook_script.encode('utf8')).hexdigest()


def read_commit_msgs(file: str):
    file_path = os.path.dirname(file)
    try:
        f = open(file)
    except FileNotFoundError:
        raise CommitMessagesFileNotFoundError(file, os.access(file_path, os.W_OK))
    with f:
        file_content = f.read().strip()
        return file_content


def create_activity(config: Config,
                    prj_config: PrjConfig,
                    commit_msgs: str,
                    remote: str):
    organization_name = prj_config.organization
    project_name = prj_config.project
    role_name = prj_config.role
    billable = False

    if not commit_msgs:
        raise EmptyCommitMessagesFileError()

    headers = generate_request_headers(config)

    organization = check_organization_exists(config, headers, organization_name)

    project = check_project_exists(config, headers, organization, project_name)

    role = check_role_exists(config, headers, project, role_name)

    now = datetime.now()
    now = now.strftime("%Y-%m-%d")
    response: Response = requests.get(config.baseURL + "activities/",
                                      params={"startDate": str(now), "endDate": str(now)},
                                      headers=headers,
                                      timeout=config.timeout)
    activities = parse_activities(response.text)
    existing_activity = find_automatic_evidence(prj_config, activities)
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
                                       timeout=config.timeout)
    if response.status_code == 200:
        print("Successfully created activity for " + project_name + " - " + role_name)


def parse_activities(response_body) -> List[Activity]:
    activities_response: List[ActivitiesResponse]
    activities_response = json.loads(response_body, object_hook=lambda x: to_class(x, cls=ActivitiesResponse))
    activities = reduce(lambda r, a: r + a.activities, activities_response, [])
    return activities


def find_automatic_evidence(prjConfig: PrjConfig, activities: List[Activity]) -> Activity:
    prefix = prjConfig.activity_prefix()
    for activity in activities:
        if prefix in activity.description and \
                prjConfig.organization == activity.organization.name and \
                prjConfig.project == activity.project.name and \
                prjConfig.role == activity.projectRole.name:
            return activity


def generate_request_headers(config):
    username, password = retrieve_keychain_credentials()
    headers = {"Authorization": "Basic " + config.basic_auth}
    payload = {"grant_type": "password",
               "username": username,
               "password": password}
    token_response = requests.post(config.authURL, headers=headers, data=payload, timeout=config.timeout)
    if token_response.status_code != 200:
        raise AuthError()
    access_token = token_response.json()["access_token"]
    headers = {"Authorization": "Bearer " + access_token}
    return headers


def retrieve_keychain_credentials():
    credentials = keyring.get_password(f"com.autentia.{NAME}", "credentials")
    # TODO: backwards compatibility. Leave only else code when all users migrated to new credentials management
    if not credentials:
        username = keyring.get_password(f"com.autentia.{NAME}", "username")
        password = keyring.get_password(f"com.autentia.{NAME}", "password")
        keyring.set_password(f"com.autentia.{NAME}", "credentials", f"{username}:{password}")
    else:
        tokens = credentials.split(sep=":", maxsplit=2)
        username = tokens[0]
        password = tokens[1]
    try:
        keyring.delete_password(f"com.autentia.{NAME}", "username")
        keyring.delete_password(f"com.autentia.{NAME}", "password")
    except PasswordDeleteError:
        # We have already deleted old values, no true error so we can continue
        pass
    if not username or not password:
        raise NoCredentialsError()
    return username, password


def check_role_exists(config, headers, project, role_name):
    response: Response = requests.get(config.baseURL + "projects/" + str(project.id) + "/roles",
                                      headers=headers, timeout=config.timeout)
    response.encoding = 'utf-8'
    if response.status_code != 200:
        raise NetworkError()
    roles: List[Role] = json.loads(response.text, object_hook=lambda x: to_class(x, cls=Role))
    role = first(lambda r: r.name == role_name, roles)
    if not role:
        raise NotFoundError("Role", role_name)
    return role


def check_project_exists(config, headers, organization, project_name):
    response: Response = requests.get(config.baseURL + "organizations/" + str(organization.id) + "/projects",
                                      headers=headers, timeout=config.timeout)
    response.encoding = 'utf-8'
    if response.status_code != 200:
        raise NetworkError()
    projects: List[Project] = json.loads(response.text, object_hook=lambda x: to_class(x, cls=Project))
    project = first(lambda p: p.name == project_name, projects)
    if not project:
        raise NotFoundError("Project", project_name)
    return project


def check_organization_exists(config, headers, organization_name):
    response: Response = requests.get(config.baseURL + "organizations", headers=headers, timeout=config.timeout)
    response.encoding = 'utf-8'
    if response.status_code != 200:
        raise NetworkError()
    organizations: List[Organization] = json.loads(response.text, object_hook=lambda x: to_class(x, cls=Organization))
    organization = first(lambda o: o.name == organization_name, organizations)
    if not organization:
        raise NotFoundError("Organization", organization_name)
    return organization


def generate_info(commit_msgs: str,
                  existing_activity: Activity = None,
                  remote_url: str = None) -> (str, datetime):

    def msg_parser(msg: str) -> Tuple[str, str, str, str]:
        if msg.count(";") != 3:
            return "", "", "", ""
        items = msg.split(";")
        return items[0], items[1], items[2], items[3]

    lines = filter(None, commit_msgs.split("\n")[::-1])
    msgs: [Tuple[str, str, datetime, str]] = list(map(msg_parser, lines))

    start_date: datetime = datetime.now().replace(hour=5, minute=0, second=0, microsecond=0, tzinfo=None)

    remote_url = "" if remote_url is None else remote_url + "\n"
    result_str: str = ""
    remote_url = formatRemoteURL(remote_url)
    if remote_url is not None and existing_activity is not None:
        remoteURLIsNew = existing_activity.description.find(remote_url) == -1
        if remoteURLIsNew:
            result_str = add_new_evidence(existing_activity, msgs, remote_url)
        if not remoteURLIsNew:
            result_str = update_existing_evidence(existing_activity, msgs, remote_url)

    else:
        result_str = add_evidence_with_no_remote_url(existing_activity, msgs, remote_url)

    # Truncate description gracefully if description buffer overflows
    result_str = (result_str[:TNT_DESCRIPTION_MAX_SIZE] + '\n...') if len(result_str) > TNT_DESCRIPTION_MAX_SIZE else result_str

    return result_str, start_date


def update_existing_evidence(existing_activity, msgs, remote_url):
    selectedDescriptionPointer: int = 0
    descriptions = ("\n" + existing_activity.description).split("\n###Autocreated evidence###\n(DO NOT DELETE)\n")

    for description in descriptions:
        if description.find(remote_url) != -1:
            break
        selectedDescriptionPointer += 1
    result_str = descriptions[selectedDescriptionPointer] + "\n-----\n"
    result_str += "\n-----\n".join(map(lambda m: "\n".join(m), msgs))
    descriptions[selectedDescriptionPointer] = result_str

    pointer = 0
    for description in descriptions:
        if description != "":
            if pointer == 1:
                result_str = "###Autocreated evidence###\n(DO NOT DELETE)\n" + description
            else:
                result_str += "\n###Autocreated evidence###\n(DO NOT DELETE)\n" + description
        pointer += 1

    return result_str


def add_new_evidence(existing_activity, msgs, remote_url):
    result_str = existing_activity.description
    result_str += "\n###Autocreated evidence###\n(DO NOT DELETE)\n" + remote_url
    result_str += "\n-----\n".join(map(lambda m: "\n".join(m), msgs))
    return result_str

def add_evidence_with_no_remote_url(existing_activity, msgs, remote_url):
    result_str = PrjConfig.activity_prefix() + "\n"
    previous_descriptions: str = ""
    if existing_activity is not None:
        previous_descriptions = existing_activity.description \
            .replace(result_str, "") \
            .replace(remote_url, "")
        previous_descriptions += "\n-----\n"
    result_str += remote_url
    result_str += previous_descriptions
    result_str += "\n-----\n".join(map(lambda m: "\n".join(m), msgs))
    return result_str
