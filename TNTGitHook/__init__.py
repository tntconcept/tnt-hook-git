import argparse
import json

from TNTGitHook.credentials import ask
from TNTGitHook.hook import create_activity, Config, PrjConfig, DEFAULT_CONFIG_FILE_PATH, NAME, read_commit_msgs
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

    args = parser.parse_args()
    config = Config.config(args.debug)

    if args.set_credentials:
        ask()
        return

    if args.setup:
        setup(config)
        return

    config_file = args.config or DEFAULT_CONFIG_FILE_PATH

    commit_msgs = args.commit_msgs if args.commit_msgs else read_commit_msgs(args.commit_msgs_file)

    with open(config_file) as config_file:
        prj_config: PrjConfig = json.load(config_file, object_hook=lambda x: to_class(x, PrjConfig))
        config.timeout = prj_config.timeout

        if is_update_needed():
            write_hook()

        try:
            create_activity(config=config,
                            prj_config=prj_config,
                            commit_msgs=commit_msgs,
                            remote=args.remote)
        except Exception as error:
            print("Could not register activity on TNT due to some errors:")
            print(error)

            if not prj_config.ignore_errors:
                exit(-1)

