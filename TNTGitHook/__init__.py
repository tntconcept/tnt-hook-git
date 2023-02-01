import argparse
import json

import requests

from TNTGitHook.credentials import ask
from TNTGitHook.exceptions import CommitMessageFormatError, InvalidSetupConfigurationError
from TNTGitHook.hook import Config, PrjConfig, DEFAULT_CONFIG_FILE_PATH, NAME, read_commit_msgs, \
    parse_commit_messages, create_activity, parse_commit_messages_from_file
from TNTGitHook.hook_setup import is_update_needed, write_hook, setup
from TNTGitHook.utils import to_class


def main(argv=None):
    parser = argparse.ArgumentParser(description=f"{NAME}")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--set-credentials", action='store_true')
    group.add_argument("--setup", action='store_true')
    group.add_argument('--commit-msgs', help="Commit messages")
    group.add_argument('--commit-msgs-file', help="Commit messages file")

    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--remote', help="Remote repo URL", required=False)
    parser.add_argument('--config', help="Config file", required=False)

    parser.add_argument('--organization', help="For setup: The organization. By default require input", required=False, default="")
    parser.add_argument('--project', help="For setup: The project. By default require input", required=False, default="")
    parser.add_argument('--role', help="For setup: The role. By default require input", required=False, default="")


    args = parser.parse_args()
    config = Config.config(args.debug)

    if args.set_credentials:
        ask()
        return

    if args.setup:
        try:
            setup(config, args.organization, args.project, args.role)
            return
        except InvalidSetupConfigurationError as error:
            print(error)
            exit(-1)

    config_file = args.config or DEFAULT_CONFIG_FILE_PATH
    try:
        commit_msgs = parse_commit_messages(args.commit_msgs) if args.commit_msgs else parse_commit_messages_from_file(args.commit_msgs_file)

        with open(config_file) as config_file:
            prj_config: PrjConfig = json.load(config_file, object_hook=lambda x: to_class(x, PrjConfig))
            config.timeout = prj_config.timeout

            if is_update_needed():
                write_hook()

            try:
                create_activity(config, prj_config, commit_msgs, args.remote)
            except requests.exceptions.RequestException as error:
                print("Timeout generating activity due to request error, continue with the push")
                print(error)
                exit(0)
            except Exception as error:
                print(" Could not register activity on TNT due to some errors:")
                print(error)

                if not prj_config.ignore_errors:
                    exit(-1)

    except Exception as error:
        print("Could not register activity on TNT due to some errors:")
        print(error)
        exit(-1)
