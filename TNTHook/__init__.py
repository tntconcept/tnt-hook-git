import argparse
import json
import os

from TNTHook.hook import create_activity, Config, ask_credentials
from TNTHook.utils import to_class


class PrjConfig:
    organization: str
    project: str
    role: str
    billable: bool


def main(argv=None):
    parser = argparse.ArgumentParser(description="TNTHook")

    parser.add_argument("--set-credentials", action='store_true')

    args = parser.parse_known_args()[0]

    if args.set_credentials:
        ask_credentials()
        return

    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--commit-msgs', help="Commit messages", required=True)
    parser.add_argument('--prev-commit-date-str', help="Previous commit date", required=False)
    parser.add_argument('--config', help="Config file", required=False)

    args = parser.parse_args()

    config_file = args.config or os.getcwd() + "/.git/hooks/tnthookconfig.json"
    with open(config_file) as config_file:
        prj_config: PrjConfig = json.load(config_file, object_hook=lambda x: to_class(x, PrjConfig))

        create_activity(Config.config(args.debug),
                        prj_config.organization,
                        prj_config.project,
                        prj_config.role,
                        prj_config.billable,
                        commit_msgs=args.commit_msgs,
                        prev_commit_date_str=args.prev_commit_date_str)
