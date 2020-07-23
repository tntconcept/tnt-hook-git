import argparse
import json
import os

from TNTGitHook.hook import create_activity, Config, ask_credentials, PrjConfig, setup, DEFAULT_CONFIG_FILE_PATH, NAME
from TNTGitHook.utils import to_class


def main(argv=None):
    parser = argparse.ArgumentParser(description=f"{NAME}")

    parser.add_argument("--set-credentials", action='store_true')
    parser.add_argument("--setup", action='store_true')
    parser.add_argument('--debug', action='store_true')

    args = parser.parse_known_args()[0]
    config = Config.config(args.debug)

    if args.set_credentials:
        ask_credentials()
        return

    if args.setup:
        setup(config)
        return

    parser.add_argument('--commit-msgs', help="Commit messages", required=True)
    parser.add_argument('--remote', help="Remote repo URL", required=False)
    parser.add_argument('--config', help="Config file", required=False)

    args = parser.parse_args()

    config_file = args.config or DEFAULT_CONFIG_FILE_PATH

    with open(config_file) as config_file:
        prj_config: PrjConfig = json.load(config_file, object_hook=lambda x: to_class(x, PrjConfig))
        config.timeout = prj_config.timeout
        try:
            create_activity(config=config,
                            prj_config=prj_config,
                            commit_msgs=args.commit_msgs,
                            remote=args.remote)
        except Exception as error:
            print("Could not register activity on TNT due to some errors:")
            print(error)

            if not prj_config.ignore_errors:
                exit(-1)

