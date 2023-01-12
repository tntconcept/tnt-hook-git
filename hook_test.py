# For Python testing newbies:
# httpretty decorator creates a server mock. You can define the response body, code, etc.
# API and documentation: https://github.com/gabrielfalcao/HTTPretty
#
# patch decorator creates a MagicMock. It must be declared using the fully qualified name of the class/function
# API and documentation: https://docs.python.org/3/library/unittest.mock.html

import json
import unittest
from typing import List
from unittest.mock import patch, MagicMock

import httpretty
import warnings

from TNTGitHook import hook, parse_commit_messages
from TNTGitHook.exceptions import AuthError, NotFoundError, NetworkError
from TNTGitHook.hook import Config, find_automatic_evidence, PrjConfig, parse_activities, generate_info
from TNTGitHook.entities import *


class HookTestCase(unittest.TestCase):

    config = Config.config(debug=True)
    fake_auth_token: str
    fake_activities: List[Activity]
    other_activities: List[Activity]
    other_activities_with_several_repos: List[Activity]
    organizationA: Organization
    organizationB: Organization
    fake_organizations: str
    projectA: Project
    projectB: Project
    json_projects: str
    roleA: Role
    roleB: Role
    json_roles: str

    def setUp(self) -> None:
        # Httpretty has an issue with unclosed file warnings. Check url for more info.
        # https://github.com/gabrielfalcao/HTTPretty/issues/368
        warnings.filterwarnings("ignore", category=ResourceWarning, message="unclosed.*")
        hook.PrjConfig.organization = "Autentia"
        hook.PrjConfig.project = "Desarrollos internos"
        hook.PrjConfig.role = "Desarrollador"
        self.setup_fake_data()

    def test_generated_info_order_should_be_from_recent_to_older(self):
        commits = hook.read_commit_msgs("new_branch_commits")
        info = generate_info(parse_commit_messages(commits), None, None)
        print(info[0])
        self.assertRegex(
            info[0],
            expected_regex=self.get_regex(),
            msg="Expected commit order doesn't comply"
        )

    def test_should_show_error_when(self):
        commits = hook.read_commit_msgs("new_branch_commits")
        info = generate_info(parse_commit_messages(commits), None, None)
        print(info[0])
        self.assertRegex(
            info[0],
            expected_regex=self.get_regex(),
            msg="Expected commit order doesn't comply"
        )

    @patch('TNTGitHook.hook.retrieve_keychain_credentials')
    @httpretty.activate(verbose=True, allow_net_connect=False)
    def test_error_retrieving_auth_token(self, mock_keyring: MagicMock):
        httpretty.register_uri(
            httpretty.POST,
            self.config.authURL,
            status=401
        )
        mock_keyring.return_value = "user", "password"
        self.assertRaises(AuthError, hook.generate_request_headers, self.config)
        # with self.assertRaises(AuthError):
        #     hook.generate_request_headers(config)

    # With patch we avoid to call the OS native keychain
    @patch('TNTGitHook.hook.retrieve_keychain_credentials')
    @httpretty.activate(verbose=True, allow_net_connect=False)
    def test_retrieve_auth_token(self, mock_credentials: MagicMock):
        httpretty.register_uri(
            httpretty.POST,
            self.config.authURL,
            status=200,
            body=self.fake_auth_token
        )
        # Training the function return value
        mock_credentials.return_value = "user", "password"

        headers = hook.generate_request_headers(self.config)
        self.assertEqual(headers, {'Authorization': 'Bearer mehmehmeh'})
        httpretty.disable()

    def test_recovery_old_credentials(self):
        with patch('keyring.get_password') as mock_get_password:
            mock_get_password.side_effect = [None, "user", "pass"]
            username, password = hook.retrieve_keychain_credentials()
        self.assertEqual("user", username)
        self.assertEqual("pass", password)

    @patch('keyring.set_password')
    def test_recovery_new_credentials(self, mock_set_password: MagicMock):
        # Patched for avoid real credential modification. Do not delete
        mock_set_password.side_effect = None
        with patch('keyring.get_password') as mock_get_password:
            mock_get_password.return_value = "user:pass"
            username, password = hook.retrieve_keychain_credentials()

        self.assertEqual("user", username)
        self.assertEqual("pass", password)

    @httpretty.activate(verbose=True, allow_net_connect=False)
    def test_organization_not_reachable(self):
        httpretty.register_uri(
            httpretty.GET,
            self.config.baseURL + "organizations",
            status=404
        )
        self.assertRaises(NetworkError, hook.check_organization_exists, self.config, "", "Not Reachable")

    @httpretty.activate(verbose=True, allow_net_connect=False)
    def test_organization_not_found(self):
        httpretty.register_uri(
            httpretty.GET,
            self.config.baseURL + "organizations",
            body=self.fake_organizations,
            status=200

        )
        self.assertRaises(NotFoundError, hook.check_organization_exists, self.config, "", "Not Exists")

    @httpretty.activate(verbose=True, allow_net_connect=False)
    def test_organization_found(self):
        httpretty.register_uri(
            httpretty.GET,
            self.config.baseURL + "organizations",
            body=self.fake_organizations,
            status=200

        )
        response = hook.check_organization_exists(self.config, "", "Test Organization")
        self.assertEqual(0, response.id)

    @httpretty.activate(verbose=True, allow_net_connect=False)
    def test_project_not_reachable(self):
        httpretty.register_uri(
            httpretty.GET,
            self.config.baseURL + "organizations/0/projects",
            status=404
        )
        self.assertRaises(NetworkError, hook.check_project_exists, self.config, "", self.organizationA, "Not Reachable")

    @httpretty.activate(verbose=True, allow_net_connect=False)
    def test_project_not_found(self):
        httpretty.register_uri(
            httpretty.GET,
            self.config.baseURL + "organizations/0/projects",
            body=self.json_projects,
            status=200

        )
        self.assertRaises(NotFoundError, hook.check_project_exists, self.config, "", self.organizationA, "Not Exists")

    @httpretty.activate(verbose=True, allow_net_connect=False)
    def test_project_found(self):
        httpretty.register_uri(
            httpretty.GET,
            self.config.baseURL + "organizations/0/projects",
            body=self.json_projects,
            status=200

        )
        response = hook.check_project_exists(self.config, "", self.organizationA, "Test Project")
        self.assertEqual(0, response.id)

    @httpretty.activate(verbose=True, allow_net_connect=False)
    def test_role_not_reachable(self):
        httpretty.register_uri(
            httpretty.GET,
            self.config.baseURL + "projects/0/roles",
            status=404
        )
        self.assertRaises(NetworkError, hook.check_role_exists, self.config, "", self.projectA, "Not Reachable")

    @httpretty.activate(verbose=True, allow_net_connect=False)
    def test_role_not_found(self):
        httpretty.register_uri(
            httpretty.GET,
            self.config.baseURL + "projects/0/roles",
            body=self.json_roles,
            status=200

        )
        self.assertRaises(NotFoundError, hook.check_role_exists, self.config, "", self.projectA, "Not Exists")

    @httpretty.activate(verbose=True, allow_net_connect=False)
    def test_role_found(self):
        httpretty.register_uri(
            httpretty.GET,
            self.config.baseURL + "projects/0/roles",
            body=self.json_roles,
            status=200

        )
        response = hook.check_role_exists(self.config, "", self.projectA, "Test Role")
        self.assertEqual(0, response.id)

    def test_find_evidence_should_return_None_if_this_is_the_first(self):
        prjConfig = PrjConfig()
        prjConfig.organization = "New Organization"
        prjConfig.project = "New Project"
        prjConfig.role = "New Role"
        self.assertIsNone(find_automatic_evidence(prjConfig, self.fake_activities))

    def test_find_evidence_should_return_activity_if_this_is_not_the_first(self):
        prjConfig = PrjConfig()
        prjConfig.organization = "Autentia Real Business Solutions S.L."
        prjConfig.project = "i+d - Desarrollos de Software Interno"
        prjConfig.role = "desarrollo"
        evidence = find_automatic_evidence(prjConfig, self.fake_activities)
        self.assertIsNotNone(evidence)
        self.assertEqual(250199, evidence.id)

    def test_find_evidence_should_return_None_if_not_first_in_project_but_first_automatic(self):
        prjConfig = PrjConfig()
        prjConfig.organization = "Autentia Real Business Solutions S.L."
        prjConfig.project = "frm - Formacion / Charlas internas"
        prjConfig.role = "AutoFormacion"
        self.assertIsNone(find_automatic_evidence(prjConfig, self.fake_activities))

    def test_generate_info(self):
        prjConfig = PrjConfig()
        prjConfig.organization = "Autentia Real Business Solutions S.L."
        prjConfig.project = "i+d - Desarrollos de Software Interno"
        prjConfig.role = "desarrollo"
        evidence = find_automatic_evidence(prjConfig, self.other_activities)
        info = generate_info(parse_commit_messages(self.commit_messages), evidence, "")
        print(info[0])
        self.assertIsNotNone(info)
        self.assertRegex(info[0], r'(^###Autocreated evidence###\n\(DO NOT DELETE\)\n)')

    def test_should_add_new_section_when_is_a_new_repository(self):
        prjConfig = PrjConfig()
        prjConfig.organization = "Autentia Real Business Solutions S.L."
        prjConfig.project = "i+d - Desarrollos de Software Interno"
        prjConfig.role = "desarrollo"
        evidence = find_automatic_evidence(prjConfig, self.other_activities)
        info = generate_info(parse_commit_messages(self.commit_messages), evidence,
                              "https://ifernandezautentia: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@github.com/ifernandezautentia/dummy-2.git")
        print(info[0])
        self.assertIsNotNone(info)
        self.assertRegex(info[0], r'(^###Autocreated evidence###\n\(DO NOT DELETE\)\n)')

    def test_generate_info_with_several_remoteURLs(self):
        prjConfig = PrjConfig()
        prjConfig.organization = "Autentia Real Business Solutions S.L."
        prjConfig.project = "i+d - Desarrollos de Software Interno"
        prjConfig.role = "desarrollo"
        evidence = find_automatic_evidence(prjConfig, self.other_activities_with_several_repos)
        info = generate_info(parse_commit_messages(self.commit_messages), evidence,
                              "https://****:****@github.com/user/dummy.git")
        print(info[0])
        self.assertIsNotNone(info)
        self.assertRegex(info[0], r'(^###Autocreated evidence###\n\(DO NOT DELETE\)\n)')

    def get_regex(self) -> str:
        header = r'(^###Autocreated evidence###\n\(DO NOT DELETE\)\n){1}'
        sha = r'([\da-f]{40}\n)'
        formatted_time = r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}\n)'
        commiter = r'(.+<.+@.+>\n)'
        commit_message = r'(.+)'
        record_separator = r'(\n-{5})?'
        return f'{header}({sha}{formatted_time}{commiter}{commit_message}{record_separator})+'

    def setup_fake_data(self):

        self.fake_auth_token = json.dumps(
            {
                "access_token": "mehmehmeh",
                "token_type": "bearer",
                "refresh_token": "mehmehmehrefresh ",
                "expires_in": 1799,
                "scope": "tnt",
                "userId": 000,
                "departmentId": 0,
                "jti": "00000000-0000-0000-0000-000000000000"
            }
        )

        with open('new_branch_commits') as commits:
            self.commit_messages = commits.read()

        with open('resources/invalid_branch_commits') as invalid_commits:
            self.invalid_commits_messages = invalid_commits.read()

        with open('example_activities') as example_activities:
            data = example_activities.read()
        self.fake_activities = parse_activities(data)

        with open('other_activities.json') as other_activities:
            data = other_activities.read()
        self.other_activities = parse_activities(data)

        with open('other_activities_with_several_repos.json') as other_activities_with_several_repos:
            data = other_activities_with_several_repos.read()
        self.other_activities_with_several_repos = parse_activities(data)

        self.organizationA = Organization().with_id(0).with_name("Test Organization")
        self.organizationB = Organization().with_id(1).with_name("Another Organization")
        self.fake_organizations = json.dumps([fake_organization.__dict__ for fake_organization in [self.organizationA, self.organizationB]])

        self.projectA = Project().with_id(0).with_name("Test Project").with_open(True).with_billable(True)
        self.projectB = Project().with_id(1).with_name("Other Project").with_open(True).with_billable(True)
        self.json_projects = json.dumps([fake_project.__dict__ for fake_project in [self.projectA, self.projectB]])

        self.roleA = Role().with_id(0).with_name("Test Role")
        self.roleB = Role().with_id(1).with_name("Other Role")
        self.json_roles = json.dumps([fake_role.__dict__ for fake_role in [self.roleA, self.roleB]])

        self.fake_remote_url = "git@github.com:autentia/TNTConcept.git"
        self.fake_activity = "This is a manual created activity by the user"
        self.fake_automatic_activity = hook.PrjConfig.activity_prefix() + "This is a manual created activity by the user"


if __name__ == '__main__':
    unittest.main()
