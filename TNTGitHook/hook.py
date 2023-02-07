from __future__ import annotations

import hashlib
import json
import os
import pkgutil
import stat
from datetime import timezone
from functools import reduce
from pathlib import Path
from typing import List, Tuple

import keyring
import requests
from keyring.errors import PasswordDeleteError
from requests import Response

from TNTGitHook.entities import *
from TNTGitHook.exceptions import NoCredentialsError, AuthError, NotFoundError, NetworkError, \
    CommitMessagesFileNotFoundError, CommitMessageFormatError, CommitMessagesFileFormatError, \
    InvalidSetupConfigurationError
from TNTGitHook.utils import DateTimeEncoder, first, to_class, formatRemoteURL, hook_installation_path

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

def setup_config(config: Config, selected_organization: str, selected_project: str, selected_role: str):
    setup_config_with_path(config, selected_organization, selected_project, selected_role, DEFAULT_CONFIG_FILE_PATH)


def setup_config_with_path(config: Config, selected_organization: str, selected_project: str, selected_role: str,
                           path: str):
    try:
        prj_config_input = check_new_setup(path, selected_organization, selected_project, selected_role)
        headers = generate_request_headers(config)
        organization = check_organization_exists(config, headers, prj_config_input[0])
        project = check_project_exists(config, headers, organization, prj_config_input[1])
        role = check_role_exists(config, headers, project, prj_config_input[2])

        prj_config = PrjConfig()
        prj_config.organization = organization.name
        prj_config.project = project.name
        prj_config.role = role.name

        if is_valid_configuration(selected_organization, selected_project, selected_role):
            with open(path, "w") as f:
                f.write(json.dumps(prj_config.__dict__, sort_keys=True, indent=4))
        else:
            print(f"********** Using project configuration found in {path}: **********\n"
                  f"Organization: {prj_config_input[0]}\n"
                  f"Project: {prj_config_input[1]}\n"
                  f"Role: {prj_config_input[2]}\n")
    except FileNotFoundError:
        print("Unable to setup config. Is this a git repository?\nMaybe you're not at the root folder.")
    except Exception as ex:
        print(ex)


def check_new_setup(path: str, organization: str, project: str, role: str):
    if not is_valid_configuration(organization, project, role):
        config_file = Path(path)
        if not config_file.is_file():
            raise InvalidSetupConfigurationError()
        else:
            file = open(config_file)
            prj_config_file = json.load(file)
            if is_valid_file_configuration(prj_config_file) \
                    and is_valid_configuration(prj_config_file["organization"], prj_config_file["project"],
                                               prj_config_file["role"]):
                return prj_config_file["organization"], prj_config_file["project"], prj_config_file["role"]
            else:
                raise InvalidSetupConfigurationError()
    else:
        return organization, project, role


def is_valid_configuration(organization: str, project: str, role: str):
    return organization and project and role


def is_valid_file_configuration(config_file):
    return "organization" in config_file and "project" in config_file and "role" in config_file


def write_hook_script():
    hook_script = pkgutil.get_data('TNTGitHook', 'misc/tnt_git_hook.sh').decode('utf8')
    try:
        hook_directory = creates_hook_directory()
        path = f"{hook_directory}tnt_git_hook"
        with open(path, "w") as file:
            file.write(hook_script)
            stats = os.stat(path)
            os.chmod(path, stats.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except FileNotFoundError:
        print(f"Unable to setup hook script. Are you able to write to {str(Path.home())}?")
    except Exception as ex:
        print(ex)


def creates_hook_directory():
    users_path = hook_installation_path()
    if not Path(users_path).exists():
        os.makedirs(users_path)
    return users_path


def removes_old_hook_file():
    try:
        exists = os.path.exists("/usr/local/bin/tnt_git_hook")
        if exists:
            print("The file exists. Trying to remove")
            os.remove("/usr/local/bin/tnt_git_hook")
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
                    commit_msgs: [Tuple[str, str, datetime, str]],
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


def parse_commit_messages(commit_msgs: str):
    def msg_parser(msg: str) -> Tuple[str, str, str, str]:
        items = msg.split(";")
        if len(items) != 4:
            raise CommitMessageFormatError()
        return items[0], items[1], items[2], items[3]

    lines = filter(None, commit_msgs.split("\n")[::-1])
    msgs: [Tuple[str, str, datetime, str]] = list(map(msg_parser, lines))
    return msgs


def parse_commit_messages_from_file(commit_msgs_file: str):
    commit_msgs: str = read_commit_msgs(commit_msgs_file)
    try:
        return parse_commit_messages(commit_msgs)
    except Exception:
        raise CommitMessagesFileFormatError(build_file_info(commit_msgs, commit_msgs_file))


def build_file_info(commit_msgs, commit_msgs_file):
    file_stats = os.stat(commit_msgs_file)
    file_info: FileInfo = FileInfo()
    file_info.file_content = commit_msgs
    file_info.path = commit_msgs_file
    file_info.path_write_permissions = os.access(commit_msgs_file, os.W_OK)
    file_info.file_ctime = datetime.fromtimestamp(file_stats.st_ctime, timezone.utc)
    file_info.file_last_modification_time = datetime.fromtimestamp(file_stats.st_mtime, timezone.utc)
    file_info.file_last_access_time = datetime.fromtimestamp(file_stats.st_atime, timezone.utc)
    file_info.file_permissions = oct(file_stats.st_mode)[-3:]
    return file_info


def generate_info(commit_msgs: [Tuple[str, str, datetime, str]],
                  existing_activity: Activity = None,
                  remote_url: str = None) -> (str, datetime):
    start_date: datetime = datetime.now().replace(hour=5, minute=0, second=0, microsecond=0, tzinfo=None)

    remote_url = "" if remote_url is None else remote_url + "\n"
    result_str: str = ""
    remote_url = formatRemoteURL(remote_url)
    if remote_url is not None and existing_activity is not None:
        remoteURLIsNew = existing_activity.description.find(remote_url) == -1
        if remoteURLIsNew:
            result_str = add_new_evidence(existing_activity, commit_msgs, remote_url)
        if not remoteURLIsNew:
            result_str = update_existing_evidence(existing_activity, commit_msgs, remote_url)

    else:
        result_str = add_evidence_with_no_remote_url(existing_activity, commit_msgs, remote_url)

    # Truncate description gracefully if description buffer overflows
    result_str = (result_str[:TNT_DESCRIPTION_MAX_SIZE] + '\n...') if len(
        result_str) > TNT_DESCRIPTION_MAX_SIZE else result_str

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
